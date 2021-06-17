"""This module implements class :class:`Graph`."""

import bisect  # Used for lexicographic sort of nodes and arcs
import math

class Graph(object):
    """This class is used to define an emergy system as a directed graph. A node
    represents a physical element of the system, such as a source, a product, a 
    split, a coproduct or a tank. An arc represents a physical link bewteen two 
    elements.
    """

    def __init__(self):
        """Construtor method."""

        # Raw data: nodes and arcs are in the order they are added by the user.
        # See methods 'add_node' and 'add_arc'.
        self.__node_data = []
        self.__arc_data = []


        # Ordered data:
        self.num_nodes = 0  # Number of nodes in the graph

        # For nodes:
        # Nodes are numbered from 0 to (self.num_nodes - 1)
        #
        # label[i] is the label of node number i. It is a string
        self.label = []

        # type[i] is the type of node number i. It is a string which is either
        # 'source', 'split', 'coproduct', 'tank' of 'product'
        self.type = []

        # node_number[i] is the node number of node with label i
        self.node_number = {}

        # successors[i] is the list of node numbers for successors of node
        # number i
        self.successors = []

        # For sources:
        # uev[i] is the unitary energy value of node number i
        self.uev = {} 

        # For tanks:
        # output_node[i] is the successor number of node number i
        self.output_node = {}

        # For arcs:
        # weight[(i,j)] is the percentage (of the outgoing flow) used by arc 
        # (i,j)
        self.weight = {}

        # is_fast[(i,j)] is True if the delay for going through arc (i,j) is 
        # less than or equal to the time step. False otherwise.
        self.is_fast = {}

        # length of arc (i,j) in m
        self.length = {}

        # diameter of arc (i,j) in m
        self.diameter = {}

        # mass density of arc (i,j) in kg/m^3
        self.mass_density = {}

        # mass[(i,j)] = mass density * length * cross_section in kg of arc (i,j)
        self.mass = {}

        # flow_rate[(i,j)] is expressed in kg / s.
        self.flow_rate = {}


    def __set_arc_param(self, i, j, weight=1.0, is_fast=True, length=1.0, 
                        diameter=1.0, mass_density=1000.0, flow_rate=1000.0):

        self.weight[(i, j)] = weight
        self.is_fast[(i, j)] = is_fast
        self.length[(i,j )] = length
        self.diameter[(i, j)] = diameter
        self.mass_density[(i, j)] = mass_density
        self.flow_rate[(i,j)] = flow_rate

        self.mass[(i, j)] = mass_density * length * (diameter/2)**2 * math.pi
        #self.mass[(i,j)] = mass


    def __normalize_nodes(self):
        """Sort nodes in lexicographic order, assign to each one a number 
        in the range [0, self.num_nodes - 1], and assign characteristics of 
        nodes (label, type, list of successors).
        """
        self.__node_data.sort()  # Sort raw data


        i = 0  # Node number
        for label, node_type in self.__node_data: 
            self.label.append(label)
            self.type.append(node_type)
            self.successors.append([])
            self.node_number[label] = i
            i += 1

        # Sort uev values of sources according to their node number
        norm_uev = {}
        for label, node_type in self.__node_data:
            if node_type == 'source':
                norm_uev[self.node_number[label]] = self.uev[label]

        self.uev = {**norm_uev}


    def __normalize_arcs(self):
        """Assign node numbers to head and tail nodes. Sort resulting arcs in
        lexicographic order.
        """
        for node, suc, weight, is_fast, length, diameter, mass_density, \
            flow_rate in self.__arc_data:
            
            i = self.node_number[node]
            j = self.node_number[suc]

            # Insert successor j of i in lexicographic order
            bisect.insort(self.successors[i], j)

            # A tank has two outgoing arcs: one for the outgoing flow, the other
            # one for the tank load, which is modelled by a loop
            if self.type[i] == 'tank':
                # Add arc for outgoing flow
                self.output_node[i] = j
                self.__set_arc_param(i, j, weight=0.0)

                # Add arc for the loop
                bisect.insort(self.successors[i], i)
                self.__set_arc_param(i, i, weight=0.0)

            else:
                self.__set_arc_param(i, j, weight, is_fast, length, diameter,
                                     mass_density, flow_rate)


    def normalize(self):
        """Sort nodes and arcs in lexicographic order."""
        self.__normalize_nodes()
        self.__normalize_arcs()

    def reachable_products(self):
        """Compute the list of products reachable from each source. A product is
        reachable from a source if there is a path from the source to the 
        product in the graph.

        :returns: a dict of {str:list of int}, where each key is a source \
        label and the associated value is the list of reachable products from \
        the source.
        """
        reachable = {}

        sources = [node for node in range(self.num_nodes)
                   if self.type[node] == 'source']

        # Graph nodes are visited by depth-first search
        for source in sources:
            reachable[source] = set()
            marked = set()
            stack = [source]

            while stack:
                top_node = stack.pop()
                marked.add(top_node)

                if (self.type[top_node] == 'product'):
                    reachable[source].add(top_node)

                for suc in [s for s in self.successors[top_node]
                            if s not in marked]:
                    stack.append(suc)

        return reachable


    def add_node(self, node_label, node_type, *args):
        """Add a node to the graph.

        :param node_label: label of the node.
        :type node_label: str or int
        :param node_type: type of the node.
        :type node_type: 'source', 'product', 'split', 'coproduct', or 'tank'
        :param \*args: unit energy value (in sej per specific unit) if node_type is 'source'.
        :type \*args: int
        """
        self.__node_data.append((str(node_label), node_type))
        self.num_nodes += 1

        if args:
            self.uev[str(node_label)] = args[0]


    def add_arc(self, node_label, suc_label, weight=1.0, is_fast=True,
                length=1.0, diameter=1.0, mass_density=1000.0, flow_rate=1000.0):
        """Add an arc to the graph.
        :param node_label: label of the head node.
        :type node_label: str or int
        :param suc_label: label of the tail node.
        :type suc_label: str or int
        :param weight: percentage of the incoming flow which follows the arc.
        :type weight: double
        :param is_fast: True if it takes at most one time step to pass through.
        :type is_fast: boolean
        :param length: length of the link (in m).
        :type length: double
        :param diameter: diameter of the link (in m).
        :type diameter: double
        :param mass_density: mass density of the matter flowing through the 
        link (in kg/m^3).
        :type mass_density: double
        :param flow_rate: flow rate of the matter flowing through the link (in 
        kg/s).
        :type flow_rate: double
        """

        self.__arc_data.append((str(node_label), str(suc_label), weight,
                               is_fast, length, diameter, mass_density,
                               flow_rate))

    def save(self, file_name):
        """Save the characteristics of the graph.

        :param file_name: name of the save file
        :type file_name: str

        Each line of the file contains the characteristics of either an element
        or a link between two elements.
        

        For a source element a line is of the form
        
            'SOURCE' LABEL PARAM1

        where
        
        - LABEL is the label of the source;
        
        - PARAM1 is the uev value of the source.


        For other types of element a line is of the form
        
            TYPE LABEL

        where 

        - TYPE is either the string 'SPLIT', 'COPRODUCT', 'TANK' or 'PRODUCT';

        - LABEL is the label of the element.


        For a link a line is of the form:
        
            'LINK' LABEL1 LABEL2 WEIGHT IS_FAST L D M F 

        where 

        - LABEL1 is the label of the head element of the link;
        
        - LABEL2 is the label of the tail element of the link;
        
        - WEIGHT is the weight of the link;

        - IS_FAST is True or False, for the time delay of the link;

        - L is the length of the link;

        - D is the diameter of the link;

        - M is the mass density of the matter flowing in the link.

        - F is the flow rate

        """

        # nodes
        with open(file_name,'w') as output_file:
            for i in range(self.num_nodes):
                label = self.label[i]
                type_ = self.type[i]

                if type_ == 'source':
                    uev = str(self.uev[i])
                    output_file.write('SOURCE ' + ' ' + label + ' ' + uev + '\n')

                elif type_ == 'split':
                    output_file.write('SPLIT ' + ' ' + label + '\n')

                elif type_ == 'coproduct':
                    output_file.write('COPRODUCT ' + ' ' + label + '\n')

                elif type_ == 'tank':
                    output_file.write('TANK ' + ' ' + label + '\n')

                elif type_ == 'product':
                    output_file.write('PRODUCT ' + ' ' + label + '\n')

            # links
            for i in range(self.num_nodes):
                i_label = self.label[i]
                for j in self.successors[i]:
                    if j != i:
                        j_label = self.label[j]
                        weight = self.weight[(i,j)]
                        is_fast = self.is_fast[(i,j)]

                        line = 'LINK ' + ' ' + i_label + ' ' + j_label
                        if is_fast != True:
                            line += ' ' + str(weight) + ' ' + str(is_fast)
                            line += ' ' + str(self.length[(i,j)])
                            line += ' ' + str(self.diameter[(i,j)])
                            line += ' ' + str(self.mass_density[(i,j)])
                            line += ' ' + str(self.flow_rate[(i,j)])
                        elif weight != 1:
                            line += ' ' + str(weight)

                        output_file.write(line + '\n')


    def load(self, file_name):
        """Load the characteristics of the graph. For the format of the file see
        method :meth:`save`.

        :param file_name: name of the load file
        :type file_name: str
        """

        with open(file_name,'r') as input_file:
            for line in input_file:
                elements = line.split()
                type_, label = elements[:2]
                
                if type_ == 'SOURCE':
                    self.add_node(label, 'source', float(elements[2]))

                elif type_ == 'SPLIT':
                    self.add_node(label, 'split')                   

                elif type_ == 'COPRODUCT':
                    self.add_node(label, 'coproduct')
                
                elif type_ == 'TANK':
                    self.add_node(label, 'tank')
                
                elif type_ == 'PRODUCT':
                    self.add_node(label, 'product')

                elif type_ == 'LINK':

                    label2 = elements[2]
                    num_param = len(elements[3:])

                    if num_param == 0:
                        self.add_arc(label, label2)

                    elif num_param == 1: # also add weight
                        self.add_arc(label, label2, float(elements[3]))

                    else:  # also add fast link indicator, length, diameter,
                           # mass density, flow rate
                        self.add_arc(label, label2, float(elements[3]),
                                     False, float(elements[5]),
                                     float(elements[6]), float(elements[7]),
                                     float(elements[8]))
