"""This module implements class :class:`SimFile`."""

class SimFile(object):
    """This class is used to simulate the behaviour of the system over time. An 
    input file is used to read input values. Emergy and empower results can be 
    saved in an output file. The format of a simulation input file is defined as
    follows:

    - The first line contains the labels of columns in the following order:
        1. Source labels for the input flows
        2. Tank labels for the outgoing flows
        3. Tank labels for the loads
        4. Arc labels for the link status. An arc label is of the form \
        'head:tail'

    - Next lines contain the values to read. Each line corresponds to an update.

    The format of a simulation output file is defined as follows:

    - The first line contains the labels of columns in the following order:
        1. Product labels for emergy values
        2. Product labels for empower values

    - Next lines contain the values saved. Each line corresponds to an update.

    :param graph: name of the input file.
    :type graph: object of class :class:`~emergylib.graph.Graph`
    :param input_name: name of the input file.
    :type input_name: str
    :param output_name: name of the output file.
    :type output_name: str   
    """

    def __init__(self, graph, input_name, output_name=None):
        """Constructor method."""

        self.__graph = graph

        self.__input_file = open(input_name,'r')

        if output_name:
            self.__output_file = open(output_name,'w')
        else:
            self.__output_file = None

        self.run = True  # Simulation is stopped if False

        # Read header
        line = self.__input_file.readline()
        columns = line.split()

        # List of nodes
        self.__node_list = [graph.node_number[i] for i in columns 
                            if ':' not in i]

         # List of arcs which have a status value in the input file
        self.__arc_list = []
        for i in range(graph.num_nodes):
            for j in graph.successors[i]:
                # Loops of tank nodes are ignored since they are always
                # operational
                if j != i:  
                    self.__arc_list.append((i,j))

        # Number of sources
        self.__num_sources = len([i for i in graph.type if i == 'source'])
        
        self.__tanks = [i for i in range(graph.num_nodes) 
                        if graph.type[i] == 'tank']

        # Number of tanks
        self.__num_tanks = len(self.__tanks)


        # If there is an output file then write product labels on the first line
        if self.__output_file:

            # Write column headers for emergy
            for i in range(graph.num_nodes):
                if graph.type[i] == 'product':
                    self.__output_file.write(graph.label[i] + ' ')

            # Write column headers for empower
            for i in range(graph.num_nodes):
                if graph.type[i] == 'product':
                    self.__output_file.write(graph.label[i] + ' ')

            self.__output_file.write('\n')


    def __fill_dictionary(self, dic, tab1, tab2, start, end):
        """Return dictionary dic filled from elements of two tables. Table 1 is 
        used for keys and table 2 is used for values.  
        """

        for pair in zip(tab1[start:end], tab2[start:end]):
            num, value = pair
            #num_node = self.__graph.node_number[num]
            if value == 'True':
                dic[num] = True
            else:
                dic[num] = float(value)
        return dic


    def read_line(self, s_flows, t_flows, t_loads, is_operational):
        """Read the current line of the input file to get source flows, tank 
        flows and loads, and link status for the current step.

        :param source_flow: flow values of sources.
        :type source_flow: dict of {int:float}
        :param tank_flow: outgoing flow value of tanks.
        :type tank_flow: dict of {int:float}
        :param tank_load: load values of tanks.
        :type tank_load: dict of {int:float}
        :param is_operational: state of arcs.
        :type is_operational: dict of {(int, int):bool}
        """
        
        line = self.__input_file.readline()

        if line:

            values = line.split()
            node_values = values[:self.__num_sources + 2*self.__num_tanks]
            arc_values = values[self.__num_sources + 2*self.__num_tanks:]

            # Fill the dictionaries of source flows, tank flows and tank loads
            # with the values read on the line 
            self.__fill_dictionary(s_flows, self.__node_list, node_values, None, 
                                   self.__num_sources)

            self.__fill_dictionary(t_flows, self.__node_list, node_values, 
                                   self.__num_sources, self.__num_sources 
                                   + self.__num_tanks)

            self.__fill_dictionary(t_loads, self.__node_list, node_values, 
                                   self.__num_sources + self.__num_tanks, None)

            self.__fill_dictionary(is_operational, self.__arc_list, arc_values, 
                                   None, None)

            # Loops of tanks are always operational
            for i in self.__tanks:
                is_operational[(i,i)] = True

        else:
            self.run = False


    def write_line(self, emergy, empower):
        """Write emergy and empower values of products for the current 
        step. A new line is added to the output file.

        :param emergy: emergy values of products.
        :type emergy: dict of {int:float}
        :param empower: empower values of products.
        :type empower: dict of {int:float}
        """
        
        for product in emergy:
            self.__output_file.write(str(emergy[product]) + ' ')

        for product in empower:
            self.__output_file.write(str(empower[product]) + ' ')
            
        self.__output_file.write('\n')


    def close(self):
        """Close input and output files."""
        self.__input_file.close()
        if self.__output_file:
            self.__output_file.close()
