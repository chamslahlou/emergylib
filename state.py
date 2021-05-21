"""This module implements class :class:`State`.""" 

class State(object):
    """This class records the state of the system at current step.

    :param graph: graph of the system.
    :type graph: object of class :class:`~emergylib.graph.Graph`
    :param time_step: delay between two updates of the system.
    :type time_step: int
    """
    def __init__(self, graph, time_step):
        """Constructor method.
        """
        self.__graph = graph  # Emergy system graph
        self.__time_step = time_step  # Delay between two updates

        # For sources:
        # source_flow[i] is the value of the flow going out of node number i
        self.source_flow = {} 

        # For tanks:
        # tank_flow[i] is the value of the flow going out of node number i
        self.__tank_flow = {}
        # tank_load[i] is the amount of flow in the tank
        self.__tank_load = {}

        # For arcs:
        # weigh[(i,j)] is the weight of arc (i,j) at current step. The weight of
        # (i,j) is the pecentage of flow which flows from i to j.
        self.weight = {}   
        # is_operational[(i,j)] is True if arc (i,j) is operational at current 
        # step. If (i,j) is not operational, no flow can go from i to j.
        self.is_operational = {}

        self.__initialize()

    def __initialize(self):
        graph = self.__graph

        for node in range(graph.num_nodes):

            node_type = graph.type[node]

            if node_type == 'tank':
                self.__tank_flow[node] = 0.0
                self.__tank_load[node] = 0.0

            elif node_type == 'source':
                self.source_flow[node] = 0.0

            # By default, all arcs are operational
            for suc in graph.successors[node]:
                self.is_operational[(node, suc)] = True
                self.weight[(node, suc)] = graph.weight[(node, suc)]

    def __update_splits_weights(self):
        """Compute weight of outgoing arcs for each split node, taking into
        account operational arcs only. By definition the sum of outgoing arc 
        weights must equal 1 (i.e. 100%).
        """

        graph = self.__graph
        
        splits = [node for node in range(graph.num_nodes)
                  if graph.type[node] == 'split']

        for node in splits:
            # List of outgoing operational arcs
            operational_arcs = [(node, suc) for suc in graph.successors[node]
                                if self.is_operational[(node, suc)]]

            total_weight = sum([graph.weight[arc] for arc in operational_arcs])

            # The weight of each operational outgoing arc is adjusted in
            # proportion to the total weight of operational outgoing arcs
            if total_weight > 0:
                for arc in operational_arcs:
                    self.weight[arc] = graph.weight[arc] / total_weight

    def __update_tanks_weights(self):
        """Compute weight of outgoing arc for each tank node."""
        graph = self.__graph
        tanks = [node for node in range(graph.num_nodes)
                 if graph.type[node] == 'tank']

        for node in tanks:
            # Current amount of flow going out of the tank
            flow = self.__tank_flow[node] * self.__time_step
            
            # Adjuste the weight
            if flow > 0:
                new_weight = flow / (flow + self.__tank_load[node])
            else:
                new_weight = 0

            # By definition, the sum of the outgoing and loop arc weights must
            # equal 1 (i.e. 100%)
            suc = graph.output_node[node]
            self.weight[(node, suc)] = new_weight
            self.weight[(node, node)] = 1.0 - new_weight

    def update(self, source_flow, tank_flow, tank_load, is_operational):
        """Set the new state for the system at current step, i.e. assign new
        flow values to sources and tanks, new load values to tanks, and indicate
        if links are working or not.

        :param source_flow: new flow values of sources.
        :type source_flow: dict of {int:float}
        :param tank_flow: new outgoing flow value of tanks.
        :type tank_flow: dict of {int:float}
        :param tank_load: load values of tanks.
        :type tank_load: dict of {int:float}
        :param is_operational: new state of arcs.
        :type is_operational: dict of {(int, int):bool}
        """

        self.source_flow = source_flow
        self.__tank_flow = tank_flow
        self.__tank_load = tank_load
        self.is_operational = is_operational

        # Compute new values of weights to take into account non operational
        # arcs
        self.__update_tanks_weights()
        self.__update_splits_weights()
