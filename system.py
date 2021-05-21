"""This module implements class :class:`System`."""

import emergylib.graph
import emergylib.state
import emergylib.ugraph
import emergylib.simfile


class System(object):
    """This class is used to model an emergy system and compute emergy and 
    empower of products.

    :param start_time: time at which the system starts.
    :type start_time: int
    :param time_step: delay between two updates of the system's state.
    :type time_step: int
    :param epsilon: accuracy for convergence computation, i.e. if a and b are \
    two double values, we say that `a = b if |a - b| <= epsilon`. \
    See class :class:`emergylib.ugraph.UGraph`.
    :type epsilon: float
    :param num_cesaro: for convergence computation using Cesàro summation. See \
    class :class:`emergylib.ugraph.UGraph`.
    :type num_cesaro: int
    :param max_steps: for convergence computation, i.e. max_steps is the \
    number of steps after which the third and fourth convergence criteria are \
    applied. See class :class:`emergylib.ugraph.UGraph`.
    :type max_steps: int
    """
    
    def __init__(self, time_step=1, epsilon=0.01, 
                 num_cesaro=5, max_steps=0):
        """Constructor method."""
        
        # Emergy graph modelling the system
        self.graph = emergylib.graph.Graph()

        # State of the system
        self.state = None

        # Unfolded version of the emergy graph
        self.__unfolded_graph = None

        # Start time is 0 by default
        self.start_time = 0

        # Current step number
        self.__current_step = 0

        # Time delay between consecutive updates of the system
        self.time_step = time_step
        
        self.epsilon = epsilon
        self.num_cesaro = num_cesaro
        self.max_steps = max_steps

        # Lists of nodes according to their type
        self.sources = []
        self.splits = []
        self.coproducts = []
        self.tanks = []
        self.products = []

        # Lists of arcs
        self.arcs = []

        # For products:
        # Amount of emergy which has reached a product
        self.__arrived_emergy = {}

        # Total emergy, i.e. sum of arrived and flowing (see method update)
        self.__emergy = {}
        self.__empower = {}

        # Public versions
        self.product_emergy = {}
        self.product_empower = {}

    def __initialize_nodes(self):
        # Call the method which assigns number to nodes and sort arcs in
        # lexicographic order
        self.graph.normalize()

        # Set type lists of nodes
        for node in range(self.graph.num_nodes):
            type_ = self.graph.type[node]
            if type_ == 'source':
                self.sources.append(node)

            elif type_ == 'split':
                self.splits.append(node)

            elif type_ == 'coproduct':
                self.coproducts.append(node)

            elif type_ == 'tank':
                self.tanks.append(node)

            elif type_ == 'product':
                self.products.append(node)


    def __initialize_arcs(self):
        """Create the list of arcs for the graph."""
        for i in range(self.graph.num_nodes):
            for j in self.graph.successors[i]:
                self.arcs.append((i,j))

    def __initialize_products(self):
        # Initialize emergy and empower values of products
        for node in self.products:
            self.__arrived_emergy[node] = 0.0
            self.__emergy[node] = 0.0
            self.__empower[node] = 0.0


    def update(self, source_flow, tank_load, tank_flow, is_operational, 
               max_accuracy=False):
        """Compute the new emergy and empower values of the products. This is 
        done in several steps:

        1. Set new flow values, load values, and state of the links.

        2. Add input nodes in the unfolded graph.

        3. Add new nodes to the unfolded graph.

        4. Compute emergy and empower of products.

        5. remove non active nodes of the unfolded graph.

        6. Increment step.

        :param source_flow: flow values of sources.
        :type source_flow: dict of {int:float}
        :param tank_flow: outgoing flow value of tanks.
        :type tank_flow: dict of {int:float}
        :param tank_load: load values of tanks.
        :type tank_load: dict of {int:float}
        :param is_operational: new state of arcs. 
        :type is_operational: dict of {(int, integer):bool}
        :param max_accuracy: use only 2 of 4 criteria for convergence \
        computation if False. See class :class:`~emergylib.ugraph.UGraph`.
        :type max_accuracy: bool
        """

        self.state.update(source_flow, tank_load, tank_flow, is_operational)

        # Create a new unfolded graph if there is no one
        if not self.__unfolded_graph:
            graph = emergylib.ugraph.UGraph(self.graph, self.state, 
                                            self.time_step, self.epsilon, 
                                            self.num_cesaro, self.max_steps)

            self.__unfolded_graph = graph

        ugraph = self.__unfolded_graph
        
        # Add new input nodes at current time
        ugraph.add_inputs()

        # Unfold the graph, i.e. add new nodes in the unfolded graph
        ugraph.unfold()

        # Call the method which computes the arrived emergy, flowing emergy and
        # empower of products at the current step
        ugraph.compute_emergy()

        if max_accuracy:
            arr_eme, flow_eme, emp = ugraph.convergence()
        else:
            arr_eme, flow_eme, emp = ugraph.convergence2()

        for p in self.products:
            num_p = ugraph.product_number[p]

            self.__arrived_emergy[p] += arr_eme[num_p]
            self.__emergy[p] = self.__arrived_emergy[p] + flow_eme[num_p]
            self.__empower[p] = emp[num_p]

            label = self.graph.label[p]
            self.product_emergy[label] = self.__emergy[p]
            self.product_empower[label] = self.__empower[p]


        # Remove nodes which are no longer active in the unfolded graph
        ugraph.clean()

        self.__current_step += 1
        ugraph.set_step(self.__current_step)

    def add_source(self, node_label, sej):
        """Add a source node to the system.

        :param node_label: label of the source.
        :type node_label: str
        :param sej: unitary emergy value in solar equivalent joule.
        :type sej: int
        """
        self.graph.add_node(node_label, 'source', sej)


    def add_split(self, node_label):
        """Add a split node to the system.

        :param node_label: label of the split.
        :type node_label: str
        """
        self.graph.add_node(node_label, 'split')

    def add_coproduct(self, node_label):
        """Add a coproduct node to the system.

        :param node_label: label of the coproduct.
        :type node_label: str
        """
        self.graph.add_node(node_label, 'coproduct')

    def add_tank(self, node_label):
        """Add a tank node to the system.

        :param node_label: label of the tank.
        :type node_label: str
        """
        self.graph.add_node(node_label, 'tank')

    def add_product(self, node_label):
        """Add a product node to the system.

        :param node_label: label of the product.
        :type node_label: str
        """
        self.graph.add_node(node_label, 'product')

    def add_link(self, node_label, suc_label, weight=1.0, is_fast=True, 
                 mass=1.0, length=1.0, diameter=1.0, mass_density=1000.0, 
                flow_rate=1000.0):
        """Add an arc between two nodes to the system.
        :param node_label: label of the head node.
        :type node_label: str or int
        :param suc_label: label of the tail node.
        :type suc_label: str or int
        :param weight: percentage of the incoming flow which follows the arc.
        :type weight: double
        :param is_fast: True if the link is working. False otherwise
        :type is_fast: boolean
        :param mass: length * density * cross_section of the link (in kg).
        :type mass: double
        :param length: of the link (in m).
        :type length: double
        :param diameter:of the link (in m).
        :type diameter: double
        :param mass_density: of the material flowing (in kg/ m^3)
        :param flow_rate: of the material flowing (in kg/s)
        """

        # VERIFIER QUE LES SOMMETS EXISTENT
        self.graph.add_arc(node_label, suc_label, weight, is_fast, mass)

    def create(self):
        """Set initial values and first state of the system."""
        self.__initialize_nodes()
        self.__initialize_arcs()
        self.__initialize_products()
        self.state = emergylib.state.State(self.graph, self.time_step)


    def __reset(self):
        """Reset initial values and create first state of the system."""
        self.__unfolded_graph = None
        self.start_time = 0
        self.__current_step = 0
        self.__initialize_products()
        self.state = emergylib.state.State(self.graph, self.time_step)


    def save(self, file_name):
        """Save the system graph.

        :param file_name: name of the save file
        :type file_name: str
        """
        self.graph.save(file_name)


    def load(self, file_name):
        """Load a system graph and create the associated system. For the format 
        of the file see method :meth:`~emergylib.graph.Graph.save`.

        :param file_name: name of the load file
        :type file_name: str
        """
        self.graph.load(file_name)
        self.create()


    def __display(self, i, t, emergy, empower):
        """Print on screen some informations of the current state."""
        print()
        print("Step", i, "--- T =", t)
        print("Emergy =", {self.graph.label[i]:emergy[i] for i in emergy})
        print("Empower =", {self.graph.label[i]:empower[i] for i in empower})


    def write_sim_header(self, output_name):
        """Write the first line of the output file.

        :param output_name: name of the output file.
        :type output_name: str
        """

        output_file = open(output_name,'w')
        
        graph = self.graph
        for i in range(graph.num_nodes):
            i_label = graph.label[i]
            for j in graph.successors[i]:
                if j != i:
                    j_label = graph.label[j]

                    output_file.write(i_label + ':' + j_label +' ')

        output_file.close()



    def __compute_empower(self, node, product, path):
        """Recursive computation of the empower of every product.
        See Olivier Le Corre and Laurent Truffet "A Rigourous Mathematical 
        Framework for Computing a Sustainability Ratio: the Emergy", Journal of 
        Environmental Informatics, 2012. doi:10.3808/jei.201200222

        http://www.jeionline.org/index.php?journal=mys&page=article&op=view&path%5B%5D=201200222

        :param node: current node.
        :type node: int
        :param product: target product.
        :type product: int
        :param path: sequence of nodes on the path from the source to the target\
        product.
        :type path: list of int
        :returns: the emergy coefficient of the current node.
        """
 
        g = self.graph

        if node == product:
            return 1

        if g.type[node] == 'source':
            suc = g.successors[node][0]
            suc_path = path[:]
            suc_path.append(suc)
            return g.sej[node] * self.__compute_empower(suc, product, suc_path)

        if g.type[node] == 'split':
            val = 0
            for suc in g.successors[node]:
                if not suc in path:
                    suc_path = path[:]
                    suc_path.append(suc)
                    val += g.weight[(node, suc)] * \
                           self.__compute_empower(suc, product, suc_path)

            return val

        if g.type[node] == 'coproduct':
            val = 0
            for suc in g.successors[node]:
                if not suc in path:
                    suc_path = path[:]
                    suc_path.append(suc)
                    val2 = self.__compute_empower(suc, product, suc_path)
                    if val2 > val:
                        val = val2
            return val

        if self.graph.type[node] == 'tank':
            suc = g.output_node[node]

            if not suc in path:
                suc_path = path[:]
                suc_path.append(suc)
                return g.weight[(node, suc)] * \
                       self.__compute_empower(suc, product, suc_path)

            else:
                return 0

        return 0


    def __run_one_input(self, source_flow, tank_flow, tank_load, is_operational, 
                        display):
        """Run a simulation for only one step. It is used for annual emergy
        computation and calibration of the max_steps value.

        :param source_flow: flow values of sources.
        :type source_flow: dict of {int:float}
        :param tank_flow: outgoing flow value of tanks.
        :type tank_flow: dict of {int:float}
        :param tank_load: load values of tanks.
        :type tank_load: dict of {int:float}
        :param is_operational: state of arcs. 
        :type is_operational: dict of {(int, integer):bool}
        :param display: print results of each computation steps if True.
        :type display: bool
        """

        # # For products:
        # emergy = {}  # Emergy
        # non_zero_step = {}  # 1st step with non zero emergy
        # variation = {}  # Difference of emergy between two updates
        # last_step = {}  # last step with no emergy variation
        # num_zero = {}  # number of steps with no emergy variation

        # for i in self.products:
        #     emergy[i] = 0
        #     non_zero_step[i] = 0
        #     variation[i] = 0
        #     last_step[i] = 0
        #     num_zero[i] = 0
       
        # It is necessary to have a max_steps value > 0 for using convergence 
        # conditions to stop the flowing.
        #self.max_steps = self.graph.num_nodes

        self.update(source_flow, tank_flow, tank_load, is_operational, False)
            
        if display:
            time = self.start_time + (self.__current_step - 1) * self.time_step
            self.__display(self.__current_step, time, self.__emergy,
                           self.__empower)

        # Next inputs are set to zero
        for i in self.sources:
            source_flow[i] = 0.0

        ugraph = self.__unfolded_graph

        # Run the simulation
        num_steps = 0
        while True:
            num_steps += 1

            self.update(source_flow, tank_flow, tank_load, is_operational, 
                        max_accuracy=True)

            if display:
                time = (self.start_time
                       + (self.__current_step -1) * self.time_step)

                self.__display(self.__current_step, time, self.__emergy,
                               self.__empower)

            #print(self.__unfolded_graph.number_of_nodes())
            if self.__unfolded_graph.number_of_nodes() == 0:
                break

    def calibrate(self, display=False):
        """Compute and set the value of class attribute `max_steps`. By default
        it is equal to 5 times the number of steps for flowing a single input.

        :param display: print results of each computation steps if True.
        :type display: bool
        """

        source_flow = {}
        tank_flow = {}
        tank_load = {}
        is_operational = {}

        # Unitary input values
        for i in self.sources:
            source_flow[i] = 1.0

        for i in self.tanks:
            tank_flow[i] = 1.0  # Flows must be able to pass through tanks
            tank_load[i] = 0.0

        for i in self.arcs:
            is_operational[i] = True

        self.max_steps = self.graph.num_nodes

        self.__run_one_input(source_flow, tank_flow, tank_load, is_operational,
                             display)

        # Experimental value
        self.max_steps = self.__current_step * 5

        self.__reset()


    def annual_emergy(self, display=False):
        """Compute annual emergy under steady state conditions.

        :param display: print results of each computation steps if True.
        :type display: bool
        """
        
        source_flow = {}
        tank_flow = {}
        tank_load = {}
        is_operational = {}

        # Unitary input values
        for i in self.sources:
            source_flow[i] = 1.0 #self.graph.sej[i]

        for i in self.tanks:
            tank_flow[i] = 1.0  # Flows must be able to pass through tanks
            tank_load[i] = 0.0

        for i in self.arcs:
            is_operational[i] = True

        self.__run_one_input(source_flow, tank_flow, tank_load, is_operational,
                             display)

        self.__reset()

    def empower(self):
        """Compute the empower of every product, i.e. the instantaneous emergy of
        every product.
        """
        for p in self.products:
            label = self.graph.label[p]
            self.product_empower[label] = 0

        for p in self.products:
            for s in self.sources:
                path = [s]
                label = self.graph.label[p]
                self.product_empower[label] += self.__compute_empower(s, p, path)


    def run_scenario(self, input_name, output_name=None, start_time=0,
                     max_accuracy=False, display=False):
        """Compute emergy and empower of products

        :param input_name: name of input file.
        :type input_name: str
        :param output_name: name of output file.
        :type output_name: str
        :param display: print results of each computation steps if True.
        :type display: bool
        """
        source_flows = {}
        tank_flows = {}
        tank_loads = {}
        is_operational = {}

        # Create a file simulation
        sim_file = emergylib.simfile.SimFile(self.graph, input_name, 
                                             output_name)

        # Read the input file line by line
        while sim_file.run:
            sim_file.read_line(source_flows, tank_flows, tank_loads, 
                               is_operational)

            self.update(source_flows, tank_flows, tank_loads, is_operational,
                        max_accuracy)

            # Save results if necessary
            if output_name:
                sim_file.write_line(self.__emergy, self.__empower)

            if display:
                time = self.start_time + (self.__current_step - 1) * \
                       self.time_step

                self.__display(self.__current_step, time, self.__emergy, 
                               self.__empower)

        sim_file.close()
