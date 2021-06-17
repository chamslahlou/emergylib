"""This module implements class :class:`UGraph`. 
It is the core of the emergy and empower computation.

It is a real-time extension of the rules of calculus proposed in 

Olivier Le Corre and Laurent Truffet "A Rigourous Mathematical Framework for 
Computing a Sustainability Ratio: the Emergy", Journal of Environmental 
Informatics, 2012. doi:10.3808/jei.201200222

http://www.jeionline.org/index.php?journal=mys&page=article&op=view&path%5B%5D=201200222


The module is written in cython and numpy for speed. For general use of cython
and numpy together see for instance:

- https://cython.readthedocs.io/en/latest/src/userguide/numpy_tutorial.html 

- https://blog.paperspace.com/faster-numpy-array-processing-ndarray-cython/
"""

#from __future__ import print_function

import numpy as np

cimport numpy as cynp
cimport cython

# Define internal types for readability 
ctypedef cynp.uint8_t   Bool
ctypedef cynp.int_t     Int
ctypedef cynp.double_t  Double
ctypedef Py_ssize_t     Index 


cdef class UGraph:
    """This class implements an unfolded version of the emergy graph.
    In the unfolded graph each node is defined by its 'node number' and the step
    at which it is created. In the following comments notation (t, i) denotes a
    node created at step t and whose number is i.
    """

    # Maximum integer value
    cdef Int _max_int
    
    # Accuracy for convergence computation, i.e. if a and b are two double type 
    # values we say that a = b if |a - b| <= epsilon.
    cdef Double EPSILON

    # Number of values for Cesàro summation. Used for convergence, see method
    # 'CesaroCriterion'
    cdef Int NUM_CESARO

    # Number of steps after which the third and fourth convergence criteria are
    # applied. See methods 'convergence' and 'convergence2'
    cdef Int MAX_STEPS

    # Instance of class 'Graph' defined in pure python. See class 'Graph'
    cdef object graph

    # Instance of class 'State' defined in pure python. See class 'State'
    cdef object state

    # Number of nodes in the unfolded graph
    cdef public int num_nodes

    # Number of products
    cdef int num_products

    # Number of sources
    cdef int num_sources

    # Nodes are numbered from 0 to (num_nodes - 1)
    # node[t, i] = True if node i occurs at step t, i.e. node (t, i) exists
    cdef public Bool[:,:] node  # numpy array
    
     # suc[t, i, j] = True if j is a suc of (t, i)
    cdef public Bool[:,:,:] suc  # numpy array

    # suc_time[t, i, j] = t_j, i.e. step of j if j is a suc of (t, i)
    cdef public Index[:,:,:] suc_time  # numpy array 
    
    # suc_weight[t, i, j] = weight of arc (t, i) -> (t', j) 
    # if (t', j) is a suc of (t, i)
    cdef public Double[:,:,:] suc_weight  # numpy array

    # num_steps[i, j] = number of steps to cross arc (i, j)
    cdef Index[:,:] num_steps  # numpy array

    # Products are numbered from 0 to num_products
    # product_node_number[i] = node number of product number i. 
    cdef Int[:] product_node_number  # numpy array

    # product_number[i] = number of product of index i
    cdef public object product_number  # python dictionary

    # Sources are numbered from 0 to num_sources
    # source_node_number[i] = node number of source number i.
    cdef Int[:] source_node_number  # numpy array

    # source_number[i] = number of source of index i
    cdef object source_number  # python dictionary

    # Type of nodes are numbered:
    # 0 for 'source', 1 for 'split', 2 for 'coproduct', 3 for 'tank', and 4 for
    # 'product'.
    cdef public Int[:] node_type  # numpy array

    cdef public int start_step  # number of initial step

    cdef int step  # number of current step

    cdef int time_step

    # eme_coef[t, s, p] = emergy coefficient at step t from source s for product
    # p
    cdef public Double[:,:,:] eme_coef  # numpy array

    # emp_coef[t, s, p] = empower coefficient at step t from source s for 
    # product p
    cdef public Double[:,:,:] emp_coef  # numpy array

    # input_value[t, s] = value of input at step t for source s
    cdef public Double[:,:] input_value  # numpy array

    # integrated_input[t, s] = value of integrated input from step t-1 to step t
    # for source s
    cdef public Double[:,:] integrated_input  # numpy array

    # active_product[t, s, p] = True if the input at step t for source s is 
    # still flowing to product p
    cdef public Bool[:,:,:] active_product  # numpy array


    # For convergence of flows:
    #
    # Since it takes several steps for an input flow to go from a source to 
    # a product and since, in many cases, an input flow arrives at a product 
    # in several parts at diferent steps, we use convegence tests for every 
    # triple (input flow, source, product) to be sure that all parts have
    # reach the products.
    # To do so we record some past values:
    #
    # last_emp_val[(t, s, p)] = emergy of the input at step t for source s that
    # must reach product p
    cdef object last_emp_val  # python dictionary

    # last_eme_val[(t, s, p)] = empower of the input at step t for source s that
    # must reach product p
    cdef object last_eme_val  # python dictionary

    # total_empower[(t, s, p)] : used by the fourth convergence criterion (see 
    # method 'convergence' below)
    cdef object total_empower  # python dictionary
           #= {}

    # If an input flow has not reached a product p we record the part still
    # flowing and the part which is arrived:
    #
    # flowing_emergy[p] = part of emergy still flowing in the network
    cdef object flowing_emergy  # python dictionary

    # arrived_emergy[p] = part of the emergy which is arrived at a product
    cdef object arrived_emergy  # python dictionary
 
    # empower[p] = current empower for product p
    cdef object empower  # python dictionary

    # reachable[s] = list of products that are reachable from source s. See
    # method 'reachable_products' of class 'Graph'.
    cdef object reachable  # python dictionary


    def __init__(self, graph, state, time_step, epsilon, num_cesaro, max_steps):
        """Constructor method.
        """

        # Set the maximum integer value to numpy maximum integer value
        self._max_int = np.iinfo(np.int).max

        self.EPSILON = epsilon
        self.NUM_CESARO = num_cesaro
        self.MAX_STEPS = max_steps 

        self.graph = graph
        self.state = state

        self.start_step = 0
        self.step = 0
        self.time_step = time_step

        self.num_nodes = graph.num_nodes

        self.reachable = graph.reachable_products()

        self.num_products = len([i for i in range(self.num_nodes) 
                                    if graph.type[i] == 'product'])

        self.num_sources = len([i for i in range(self.num_nodes)
                                     if graph.type[i] == 'source'])


        self.node_type = np.zeros((self.num_nodes), dtype='int')
        self.product_node_number = np.zeros((self.num_products), dtype='int')
        self.source_node_number = np.zeros((self.num_sources), dtype='int')

        # Compute the number of steps to cross every arc of the graph
        self.num_steps = np.zeros((self.num_nodes, self.num_nodes), dtype='int')
        g = self.graph
        for i in range(self.num_nodes):
            suc = g.successors[i]
            for j in suc:
                link = (i, j)
                if i == j or g.is_fast[link]:
                    self.num_steps[i, j] = 1
                else:
                    delay = g.mass[link] / g.flow_rate[link]
                    # Casting of python int
                    self.num_steps[i, j] = <Index> round(delay / self.time_step)

        # Assign to each product a number from 0 to num_product - 1 and its node
        # number
        # Assign to each source a number from 0 to num_source - 1 and its node
        # number
        self.product_number = {}
        self.source_number = {}
        num_p = 0
        num_s = 0
        conv_type = {'source':0, 'split':1, 'coproduct':2, 'tank':3, 'product':4}
        for i in range(self.num_nodes):
            node_type = graph.type[i]
            self.node_type[i] = conv_type[node_type]

            if node_type == 'product':
                self.product_number[i] = num_p
                self.product_node_number[num_p] = i
                num_p += 1
            elif node_type == 'source':
                self.source_node_number[num_s] = i
                self.source_number[i] = num_s
                num_s += 1

        # Initialisation for convergence tests:
        self.last_eme_val = {}     
        self.last_emp_val = {}
        self.total_empower = {}

        self.arrived_emergy = {}    
        self.flowing_emergy = {}
        self.empower = {}


        # Creation of the unfolded graph for the first step
        self.first_step()


    cdef first_step(self):
        """Create graph data for the first step. The graph is represented by 
        several numpy arrays:
        
        - node
        - suc
        - suc_time
        - suc_weight
        - integrated_input
        - input_value
        - active_product

        Dimensions of the arrays are initialized.
        """

        # dimensions: 1 step, number of nodes
        dim1 = self.num_nodes
        self.node = np.zeros( (1, dim1), dtype='bool' )

        # dimensions: 1 step, number of nodes, number of nodes
        self.suc = np.full((1, dim1, dim1), False, dtype='bool')

        # dimensions: 1 step, number of nodes, number of nodes
        self.suc_time = np.full((1, dim1, dim1), self._max_int, dtype=np.int64)

        # dimensions: 1 step, number of nodes, number of nodes
        self.suc_weight = np.zeros( (1, dim1, dim1), dtype='double' )


        # dimensions: 1 step, number of sources
        dim2 = self.num_sources
        self.integrated_input = np.zeros( (1, dim2), dtype='double' )
        self.input_value = np.full( (1, dim2), -1.0, dtype='double' )

        # dimensions: 1 step, number of products
        dim3 = self.num_products
        self.active_product = np.zeros( (1, dim2, dim3), dtype='bool' )


    cdef extend(self, num_steps):
        """Add num_steps rows to graph arrays. Rows are added at the end."""

        dim1 = num_steps
        dim2 = self.num_nodes
        dim3 = self.num_products
        dim4 = self.num_sources


        node = np.zeros((dim1, dim2), dtype='bool')
        self.node = np.vstack((self.node, node))

        suc = np.full((dim1, dim2, dim2), False, dtype='bool') #V6
        self.suc = np.vstack((self.suc, suc))   #V6

        suc_time = np.full((dim1, dim2, dim2), self._max_int, dtype=np.int64)
        self.suc_time = np.vstack((self.suc_time, suc_time))       
        
        suc_weight = np.zeros((dim1, dim2, dim2), dtype='double')
        self.suc_weight = np.vstack((self.suc_weight, suc_weight))

        int_inp = np.zeros((dim1, dim4), dtype='double')
        self.integrated_input = np.vstack((self.integrated_input, int_inp))
        
        inp = np.full((dim1, dim4), -1.0, dtype='double')
        self.input_value = np.vstack((self.input_value, inp))
       
        act_prod = np.zeros((dim1, dim4, dim3), dtype='bool')
        self.active_product = np.vstack((self.active_product, act_prod))


    cdef reduce(self, num_steps):
        """Remove num_steps rows of graph arrays. Rows are removed from the 
        beginning."""

        self.node = self.node[num_steps:]
        self.suc_time = self.suc_time[num_steps:]
        self.suc_weight = self.suc_weight[num_steps:]
        self.suc = self.suc[num_steps:]
        self.input_value = self.input_value[num_steps:]
        self.integrated_input = self.integrated_input[num_steps:]
        self.active_product = self.active_product[num_steps:]


    cdef add_node(self, t, num_node):
        """Add node (t, num_node) to the graph."""

        #last_time = self.start_step + len(self.node) - 1
        last_step = len(self.node) - 1
        if t > last_step:
            self.extend(t - last_step)
        if not self.node[t - self.start_step, num_node]:
            self.node[t - self.start_step, num_node] = True


    cdef add_successors(self, num_node, suc_list):
        """Add successors of node num_node to the graph. Successors are given by
        suc_list.
        """

        t = self.step - self.start_step
        for num_suc, t_suc, weight in suc_list:

            self.add_node(t_suc, num_suc)

            self.suc[t, num_node, num_suc] = True
            self.suc_time[t, num_node, num_suc] = t_suc
            self.suc_weight[t, num_node, num_suc] = weight


    def number_of_nodes(self):
        """Compute and return the number of nodes in the graph.
        """
        cdef Index t
        cdef Index node
        cdef int n

        n = 0
        # for t in range(len(self.node)):
        #     for node in range(self.num_nodes):
        #         if self.node[t, node]:
        #             n += 1

        return np.count_nonzero(self.active_product)
        return n

    # Wrapper for python access
    def set_step(self, step):
        self.step = step


    cdef compute_inputs(self):
        """Return a list of inputs for current step. An input is a pair 
        (t, s) where t is the step and s is the source."""

        inputs = []
        for source in range(self.num_sources):
            s = self.source_node_number[source]
            flow = self.state.source_flow[s]

            val = flow * self.graph.uev[s] * self.time_step
            #print('input',s,': flow ->', flow, 'uev ->', self.graph.uev[s])
            #val = flow * self.time_step

            if val > 0:
                self.input_value[self.step - self.start_step, source] = val

                inputs.append((self.step, source))

            else:
                # If there is no input value we check if there is an input at
                # the previous step. In this case the zero input value is added
                # to the list. This allows integration of consecutive input
                # values.
                previous_step = self.step - 1
                if previous_step >= self.start_step:

                    t = previous_step - self.start_step
                    if self.input_value[t, source] > 0:

                        t = self.step - self.start_step
                        self.input_value[t, source] = 0.0

                        inputs.append((self.step, source))

        return inputs


    cdef compute_integrated_inputs(self, inputs):
        """Compute integration of inputs of current step. For each input of 
        current step, its integrated value is the average of the current input
        value and the input value at the previous step.
        """

        cdef Index offset

        for t, source in inputs:
            previous = 0.0

            previous_time = self.step - 1
            if previous_time >= self.start_step :
                previous_val = self.input_value[previous_time - self.start_step,
                                                source]

                if previous_val > 0:
                    previous = previous_val

            flow = self.input_value[self.step - self.start_step, source]
            offset = t - self.start_step
            self.integrated_input[offset, source] = 0.5 * (previous + flow)


    cdef add_input_nodes(self, inputs):
        """Add a node (t, s) for each input of list inputs.
        """

        for t, source in inputs:
            s = self.source_node_number[source]
            self.add_node(t, s)

            # Initialize convergence data for each input and each product which
            #  is reachable from the input source
            for product in self.reachable[s]:

                p = self.product_number[product] 

                self.active_product[t - self.start_step, source, p] = True

                self.last_eme_val[(t, source, p)] = []
                self.last_emp_val[(t, source, p)] = []
                self.total_empower[(t, source, p)] = 0.0


    cdef remove_inactive_inputs(self):
        """Remove inactive input nodes and their associated data. An input node
        is inactive if no flow goes from the source of the input to any product. 
        """

        inactives_inputs = []

        for source in range(self.num_sources):
            for t in range(self.step - self.start_step + 1):
                if self.input_value[t, source] >= 0:
                # If (source, time) is an input we check if it is still active
                    inactive = True
                    s = self.source_node_number[source]
                    for p in self.reachable[s]:
                        product = self.product_number[p]
                        if self.active_product[t, source, product]:
                            inactive = False
                
                    if inactive:
                        inactives_inputs.append((t, source))
        
        # Set values for inactive input nodes and their associated data
        for t, source in inactives_inputs:
            s = self.source_node_number[source]
            self.node[t, s] = False

           # Since an input value can be equal to zero (see method 
            # compute_inputs) value -1 is used to 
            self.input_value[t, source] = -1.0
            self.integrated_input[t, source] = -1.0


    cdef find_earliest_active_source(self):
        """Return the first step at which there is an active source."""

        for t in range(self.step - self.start_step + 1):
            for source in range(self.num_sources):
                if self.input_value[t, source] >= 0:  # if active source
                    return t
        return t # to avoid return of 'NoneType' if there is no active source


    cdef remove_nodes_before_start_step(self):
        """Remove all nodes which are before the earliest active source."""

        t = self.find_earliest_active_source()

        if t >= 0:
            self.start_step += t
            self.reduce(t)


    def compute_emergy(self):
        """Compute emergy and empower of products for current step."""
        
        dim1 = self.step - self.start_step + 1
        dim2 = self.num_nodes
        dim3 = self.num_products
 
        # Set numpy arrays for computing emergy and empower coefficients
        self.eme_coef = np.zeros((dim1, dim2, dim3), dtype='double')
        self.emp_coef = np.zeros((dim1, dim2, dim3), dtype='double')
 

        self.emergy_coefficients()
        self.empower_coefficients()


    def clean(self):
        """Remove inactive nodes for current step."""

        self.remove_inactive_inputs() 
        self.remove_nodes_before_start_step()


    def add_inputs(self):
        """Add new inputs for current step."""

        inputs = self.compute_inputs()

        if inputs:
            self.compute_integrated_inputs(inputs)
            self.add_input_nodes(inputs)
        else:
            self.extend(1)  # add one step with no nodes to the unfolded graph


    def unfold(self):
        """Add successors of nodes which are at current step.
        """
        # offset = index of current step for numpy arrays 
        offset = self.step - self.start_step
        
        if offset < len(self.node):
            for node in range(self.num_nodes):
                # For nodes at current step
                if self.node[offset, node]:
                    suc_list = [suc for suc in self.graph.successors[node] 
                                if self.state.is_operational[(node, suc)]]

                    suc_info = []
                    for suc in suc_list:
                        t_suc = self.step + self.num_steps[node, suc]
                        weight = self.state.weight[(node, suc)]
                        suc_info.append((suc, t_suc, weight))

                    self.add_successors(node, suc_info)


    cdef inline double sum_suc_eme_coef(self, Index time, Index node, Index p):
        """Return the value of the emergy coefficient of 'node', i.e. sum over
        successors j of 'node' of expression 

                w[j] * coef[j]

        where:
        - w[j] = weight of link (node, j)
        - coef[j] = emergy cooefficient of node j.
        """

        cdef double val = 0.0

        cdef Index t
        cdef Index t_suc
        cdef Index suc

        t = time - self.start_step
        for suc in range(self.num_nodes):
            if self.suc[t, node, suc]: #V6 
                t_suc = self.suc_time[t, node, suc]
                if t_suc <= self.step:
                    val += (self.suc_weight[t, node, suc]
                            * self.eme_coef[t_suc - self.start_step, suc, p])

        return val


    cdef inline double max_suc_eme_coef(self, Index time, Index node, Index p):
        """Return the value of the emergy coefficient of 'node', i.e. maximum
        over successors j of 'node' of expression 

                w[j] * coef[j]

        where:
        - w[j] = weight of link (node, j)
        - coef[j] = emergy cooefficient of node j.
        """

        cdef double val = 0.0
        cdef double val2

        cdef Index t
        cdef Index t_suc
        cdef Index suc

        t = time - self.start_step
        for suc in range(self.num_nodes):
            if self.suc[t, node, suc]: #V6 
                t_suc = self.suc_time[t, node, suc]
                if t_suc <= self.step:
                    val2 = (self.suc_weight[t, node, suc] 
                            * self.eme_coef[t_suc - self.start_step, suc, p])
                    if val2 > val:
                        val = val2
        return val


    cdef inline double sum_suc_emp_coef(self, Index time, Index node, Index p):
        """Return the value of the empower coefficient of 'node', i.e. sum over
        successors j of 'node' of expression 

                w[j] * coef[j]

        where:
        - w[j] = weight of link (node, j)
        - coef[j] = empower cooefficient of node j.
        """

        cdef double val = 0.0

        cdef Index t
        cdef Index t_suc
        cdef Index suc

        t = time - self.start_step
        for suc in range(self.num_nodes):
            if self.suc[t, node, suc]: #V6 
                t_suc = self.suc_time[t, node, suc]
                if t_suc <= self.step:
                    val += (self.suc_weight[t, node, suc] 
                            * self.emp_coef[t_suc - self.start_step, suc, p])

        return val


    cdef inline double max_suc_emp_coef(self, Index time, Index node, Index p):
        """Return the value of the empower coefficient of 'node', i.e. maximum
        over successors j of 'node' of expression 

                w[j] * coef[j]

        where:
        - w[j] = weight of link (node, j)
        - coef[j] = empower cooefficient of node j.
        """

        cdef double val = 0.0
        cdef double val2

        cdef Index t
        cdef Index t_suc
        cdef Index suc

        t = time - self.start_step
        for suc in range(self.num_nodes):
            if self.suc[t, node, suc]: #V6 
                t_suc = self.suc_time[t, node, suc]
                if t_suc <= self.step:
                    val2 = (self.suc_weight[t, node, suc] 
                            * self.emp_coef[t_suc - self.start_step, suc, p])
                    if val2 > val:
                        val = val2
        return val


    cdef emergy_coefficients(self):
        """Compute emergy coefficients of all nodes for current step.
        """

        cdef double emergy = 0.0

        cdef Index product
        cdef Index time
        cdef Index t
        cdef Index node

        cdef int type_

        for product in range(self.num_products):

            for time in range(self.step, self.start_step - 1 , -1) :

                t = time - self.start_step
                for node in range(self.num_nodes):

                    if self.node[t, node]:

                        emergy = 0.0

                        type_ = self.node_type[node]
                        if type_ == 4:  # product

                            if node == self.product_node_number[product]:
                                
                                emergy = 1.0

                        elif type_ == 1 or type_ == 3:  # split or tank

                            emergy = self.sum_suc_eme_coef(time, node, product) 

                        elif type_ == 2:    # coproduct

                            emergy = self.max_suc_eme_coef(time, node, product)

                        elif type_ == 0:    # source
                            source = self.source_number[node]

                            if self.active_product[t, source, product] :
                                emergy = (self.sum_suc_eme_coef(time, 
                                                                node, product) 
                                            * self.integrated_input[t, source])

                        self.eme_coef[t, node, product] = emergy


    cdef empower_coefficients(self):
        """Compute empower coefficients of all nodes for current step.
        """

        cdef double empower = 0.0

        cdef Index product
        cdef Index time
        cdef Index t
        cdef Index node

        cdef int type_
        
        for product in range(self.num_products):

            for time in range(self.step, self.start_step - 1, -1):

                t = time - self.start_step
                for node in range(self.num_nodes):

                    if self.node[t, node]:
                        empower = 0.0

                        type_ = self.node_type[node]

                        if type_ == 4:  # product

                            if node == self.product_node_number[product]:
                                if time == self.step:
                                    empower = 1.0

                        elif type_ == 1 or type_ == 3:  # split or tank

                            empower = self.sum_suc_emp_coef(time, node, product) 

                        elif type_ == 2:    # coproduct

                            empower = self.max_suc_emp_coef(time, node, product) 

                        elif type_ == 0:    # source
                            source = self.source_number[node]
                            
                            if (self.active_product[t, source, product]
                                and self.input_value[t, source] > 0):

                                empower = (self.sum_suc_emp_coef(time, 
                                                                 node, product) 
                                            * self.integrated_input[t, source]
                                            / self.time_step)

                        self.emp_coef[t, node, product] = empower


    cdef inline set_arrived(self, Index t, Index s, Index p, double eme, 
                            double emp):
        """Add arrived emergy and empower."""

        self.arrived_emergy[p] += eme
        self.empower[p] += emp

        # Product p is not active anymore
        self.active_product[t - self.start_step, s, p] = False
        
        # Remove dictionaries of past values
        del self.last_eme_val[(t, s, p)]
        del self.last_emp_val[(t, s, p)]      
        del self.total_empower[(t, s, p)]


    cdef inline set_flowing(self, Index p, double eme, double emp):
        """Add current emergy and empower flows for product p."""

        self.flowing_emergy[p] += eme
        self.empower[p] += emp  

    cdef inline Bool CesaroCriterion(self, int t, int s, int p):
        """Check if the mean of the last empower positive values is negligible
        compared to the mean of the first NUM_CESARO postive empower value (see
        function 'coonvergence')
        """

        cdef int val
        cdef double emp_sum
        cdef double val_emp

        val = 0
        emp_sum = 0
        for val_emp in self.last_emp_val[(t, s, p)]:
            emp_sum += val_emp
            if val_emp > 0:
                val += 1

        if (val > 0) and (emp_sum / val) < (self.total_empower[(t, s, p)] 
                                            / self.NUM_CESARO * self.EPSILON) :

            return True
        else:
            return False


    cdef inline increaseCesaro(self, int t, int s, int p, double emp):
        """Record flowing empower from source number s to product number p at 
        step t.
        """

        self.last_emp_val[(t, s, p)].append(emp)
        self.total_empower[(t, s, p)] += emp


    def convergence(self):
        """Compute the arrived_emergy, flowing_emergy and empower of every
        product for every input. Four criteria are used to check if the 
        remaining flowing emergy is negligible and thus the input can be
        considered as fully arrived to the product.
        """

        cdef Index source, prod, t, time

        cdef double eme, emp, int_input, val

        cdef list last_eme, last_emp

        for prod in range(self.num_products) :
            self.arrived_emergy[prod] = 0.0
            self.flowing_emergy[prod] = 0.0
            self.empower[prod] = 0.0

            for source in range(self.num_sources):
                for time in range(self.step, self.start_step - 1, -1):
                    t = time - self.start_step
                    
                    if self.active_product[t, source, prod]:
                        s = self.source_node_number[source]
                        eme = self.eme_coef[t, s, prod]
                        emp = self.emp_coef[t, s, prod]
                        
                        last_eme = self.last_eme_val[(time, source, prod)]
                        last_emp = self.last_emp_val[(time, source, prod)]

                        int_input = self.integrated_input[t, source]

                        # Criterion 1
                        if (1.0 - emp * self.time_step / int_input 
                            <= self.EPSILON):

                            val = self.input_value[t, source] / self.time_step
                            self.set_arrived(time, source, prod, int_input, val)

                        # Criterion 2
                        elif (1.0 - eme / int_input) <= self.EPSILON:
                            self.set_arrived(time, source, prod, int_input, 0.0)

                        else:
                            last_eme.append(eme)

                            if time + self.MAX_STEPS > self.step :
                                self.set_flowing(prod, eme, emp)

                                # Record up to 'NUM_CESARO' non zero empower 
                                # values
                                if emp > 0 and len(last_emp) < self.NUM_CESARO:
                                    self.increaseCesaro(time, source, prod, emp)

                            else:
                                # Criterion 3
                                if (eme - last_eme[0] <= self.EPSILON * eme):
                                    self.set_arrived(time, source, prod, eme, 
                                                     0.0)

                                else:

                                    del last_eme[0]

                                    if len(last_emp) < self.NUM_CESARO:
                                        self.set_flowing(prod, eme, emp)
                                        if emp > 0:
                                            self.increaseCesaro(time, source, 
                                                                prod, emp)

                                    else:
                                        # Criterion 4
                                        if self.CesaroCriterion(time, source, 
                                                                prod):

                                            self.set_arrived(time, source, prod, 
                                                                eme, 0.0)

                                        else:
                                            self.set_flowing(prod, eme, emp)
                                            del last_emp[0]
                                            last_emp.append(emp)

        return (self.arrived_emergy, self.flowing_emergy, self.empower)


    def convergence2(self):
        """Same as 'convergence' method but without third and fourth criteria.
        """

        cdef Index source, prod, t, time

        cdef double eme, emp, int_input, val

        cdef list last_eme, last_emp

        for prod in range(self.num_products) :
            self.arrived_emergy[prod] = 0.0
            self.flowing_emergy[prod] = 0.0
            self.empower[prod] = 0.0

            for source in range(self.num_sources):
                for time in range(self.step, self.start_step - 1, -1):
                    t = time - self.start_step
                    if self.active_product[t, source, prod]:

                        s = self.source_node_number[source]
                        eme = self.eme_coef[t, s, prod]
                        emp = self.emp_coef[t, s, prod]
                        
                        last_eme = self.last_eme_val[(time, source, prod)]
                        last_emp = self.last_emp_val[(time, source, prod)]

                        int_input = self.integrated_input[t, source]

                        # Criterion 1
                        if (1.0 - emp * self.time_step / int_input 
                            <= self.EPSILON):

                            val = self.input_value[t, source] / self.time_step
                            self.set_arrived(time, source, prod, int_input, val)

                        # Criterion 2
                        elif (1.0 - eme / int_input) <= self.EPSILON:
                            self.set_arrived(time, source, prod, int_input, 0.0)

                        else:
                            self.set_flowing(prod, eme, emp)

        return (self.arrived_emergy, self.flowing_emergy, self.empower)