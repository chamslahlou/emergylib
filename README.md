# emergylib
A python library for computing emergy

# Authors
Chams Lahlou, Olivier Le Corre and Laurent Truffet


# Overview

This library allows to compute three kinds of emergy:
    - annual emergy under steady state conditions,
    - empower, i.e. the instantaneous emergy,
    - real-time emergy.

More precisely, with this library one can:

model systems with elements such as sources, splits, coproducts, tanks and products:

    network = emsys.System()
    network.add_source('Sun', 1200000.0)
    network.add_split('Solar panel')
    network.add_product('car')
    network.add_link('Sun', 'Solar panel')
    network.add_link(Solar panel', 'car')

load and save modelling of systems:
    
    network.load('factory.txt')
    ...
    network.save('factory2.txt')

compute emergy and empower of products in steady-state:

    for i in network.sources:
        source_flow[i] = 1.0

    for i in network.tanks:
        tank_flow[i] = 1.0
        tank_load[i] = 0.0

    for i in network.arcs:
        is_operational[i] = True

    network.run_steady_state(source_flow, tank_flow, tank_load, 
                             is_operational, display=True)

compute emergy and empower of products in real-time:

    network.run_scenario('sim_data.txt','results.txt', display=True)

# Emergy Network Builder

There are three ways to define a system network for which we want to compute emergy:
    - directely by editing a text file. In this case, each line defines a component of the system (a source, split, ...) or a link between two coponents. The format is documented in function :meth:`~emergylib.graph.Graph.save`.
    - by adding components and links in the python program, and by saving the resulting network in a file. This will be illustrated in the step-by-step example below.
    - by using our graphical tool, called 'emergy Network Builder'. It is not documented, but very simple and intuitive to use. It uses tkinter the python library for the Tk Graphical User Interface (see https://docs.python.org/3/library/tkinter.html).

    ![alt text](https://github.com/chamslahlou/emergylib/images/emergylib_network_builder.png?raw=true)


# Installation

1. Install Python 3 if necessary.

2. Install Cython if necessary.

3. Download emergy package.

4. Unzip the package


Compile cython module by:

    python setup-ugraph.py build_ext --inplace

# Step-by-step example

Let us consider the following example (from Li et al, Emergy Algebra: Improving Matrix Method for Calculating Transformities, Ecological Modelling 221, (411- 422) https://doi.org/10.1016/j.ecolmodel.2009.10.015:

.. image:: exemple.png

Under a terminal, launch python, then import the module 'system' of the library:

    >>> import emergylib.system as emsys

We create an empty network:

    >>> network = emsys.System()

We add the components of the system:

    >>> network.add_source(1, 1000)
    >>> network.add_source(2, 500)
    >>> network.add_split(3)
    >>> network.add_coproduct(4)
    >>> network.add_split(5)
    >>> network.add_split(6)
    >>> network.add_split(7)
    >>> network.add_split(8)
    >>> network.add_split(9)
    >>> network.add_split(10)
    >>> network.add_product(11)
    >>> network.add_product(12)
    >>> network.add_product(13)
    >>> network.add_product(14)

We connect the components:

    >>> network.add_link(1, 3)
    >>> network.add_link(2, 10)
    >>> network.add_link(3, 4, 0.625)
    >>> network.add_link(3, 5, 0.375)
    >>> network.add_link(4, 6)
    >>> network.add_link(4, 7)
    >>> network.add_link(5, 7, 0.8)
    >>> network.add_link(5, 14, 0.2)
    >>> network.add_link(6, 8, 0.8)
    >>> network.add_link(6, 9, 0.2)
    >>> network.add_link(7, 9, 0.66667)
    >>> network.add_link(7, 10, 0.33333)
    >>> network.add_link(8, 12)
    >>> network.add_link(9, 13)
    >>> network.add_link(10, 11, 0.66667)
    >>> network.add_link(10, 4, 0.33333)

And finally we create the network:

    >>> network.create()

Now, it is possible to save the resulting network:

    >>> network.save('network_li_et_al.txt')

The empower, i.e. instantaneous emergy, of the system is obtained by:

    >>> network.empower()
    >>> print(network.product_empower)
    {'11': 538.8895277675, '12': 659.998133336, '13': 734.4468388839999, '14': 75.00000000000001}

In order to compute annual emergy or run a simulation we need to calibrate the convergence parameters:

    >> network.calibrate()
    >> print(network.max_steps)
    135

The annual emergy (under steady state conditions) of the system is obtained by:

    >>> network.annual_emergy()
    >>> print(network.product_emergy)
    {'11': 606.2485694420819, '12': 659.998133336, '13': 818.7499410791447, '14': 75.00000000000001}
    >>> print(network.product_empower)
    {'11': 0.0, '12': 0.0, '13': 0.0, '14': 0.0}

A simulation is defined by a sequence of steps where, for each time step, the values of the inputs and the status of the links (working or not) are given. 

A simulation can be defined by giving these values in a program, or by loading a file which contains these values.
The format a simulation file is documented in module :meth:`~emergylib.simfile.SimFile`. Here are the first lines of the file sim_Li_et_al.txt (see in folder 'example'). The first line gives the labels of the sources and the labels of connections. The following lines give the input of the sources at each step and the state of each connection. The input flow is the product of the source sej by the input value. For example, at the first step we have 1000 * 0.5 = 500 sej for source 1 and 500 * 0.2 = 100 sej for source 2; at the second step we have 500 sej for source 1 and 400 sej for source 2:

    1   2   1:3 2:10    3:4 3:5 4:6 4:7 5:7 5:14    6:8 6:9 7:9 7:13    8:12    9:13    10:4    10:11
    1   1   True    True    True    True    True    True    True    True    True    True    True    True    True    True    True    True
    0   0   True    True    True    True    True    True    True    True    True    True    True    True    True    True    True    True
    0   0   True    True    True    True    True    True    True    True    True    True    True    True    True    True    True    True


In our case we use the file sim_Li_et_al.txt (see in folder 'example') an run the simulation with options 'max accuracy' and 'display':

    >>> network.run_scenario('sim_Li_et_al.txt','results.txt', max_accuracy=True, display=True)

    Step 1 --- T = 0
    Emergy = {'11': 0.0, '12': 0.0, '13': 0.0, '14': 0.0}
    Empower = {'11': 0.0, '12': 0.0, '13': 0.0, '14': 0.0}

    Step 2 --- T = 1
    Emergy = {'11': 0.0, '12': 0.0, '13': 0.0, '14': 0.0}
    Empower = {'11': 0.0, '12': 0.0, '13': 0.0, '14': 0.0}

    Step 3 --- T = 2
    Emergy = {'11': 33.3335, '12': 0.0, '13': 0.0, '14': 0.0}
    Empower = {'11': 33.3335, '12': 0.0, '13': 0.0, '14': 0.0}

    Step 4 --- T = 3
    Emergy = {'11': 200.00099999999998, '12': 0.0, '13': 0.0, '14': 18.750000000000004}
    Empower = {'11': 166.6675, '12': 0.0, '13': 0.0, '14': 18.750000000000004}

    Step 5 --- T = 4
    Emergy = {'11': 333.335, '12': 0.0, '13': 0.0, '14': 56.250000000000014}
    Empower = {'11': 0.0, '12': 0.0, '13': 0.0, '14': 37.50000000000001}

    Step 6 --- T = 5
    Emergy = {'11': 388.42728009002315, '12': 138.3332, '13': 165.278493055, '14': 75.00000000000001}
    Empower = {'11': 55.092280090023145, '12': 138.3332, '13': 165.278493055, '14': 0.0}

    Step 7 --- T = 6
    Emergy = {'11': 509.72278471451386, '12': 454.9992, '13': 529.1686458300001, '14': 75.00000000000001}
    Empower = {'11': 121.29550462449075, '12': 316.666, '13': 363.890152775, '14': 0.0}

    Step 8 --- T = 7
    Emergy = {'11': 575.9260092489815, '12': 633.3320000000001, '13': 727.7803055500001, '14': 75.00000000000001}
    Empower = {'11': 0.0, '12': 0.0, '13': 0.0, '14': 0.0}

    Step 9 --- T = 8
    Emergy = {'11': 582.0472512767516, '12': 639.9985333340001, '13': 746.1442152724076, '14': 75.00000000000001}
    Empower = {'11': 6.121242027770066, '12': 22.036581483981486, '13': 18.36390972240742, '14': 0.0}

    Step 10 --- T = 9
    Emergy = {'11': 595.5242600241436, '12': 653.3316000020002, '13': 786.5756458288888, '14': 75.00000000000001}
    Empower = {'11': 13.477008747391983, '12': 48.51747408040741, '13': 40.43143055648151, '14': 0.0}

    ...

    Step 46 --- T = 45
    Emergy = {'11': 606.2492031229698, '12': 659.9981333360001, '13': 818.7507968768783, '14': 75.00000000000001}
    Empower = {'11': 4.770667687633022e-11, '12': 1.717448954878535e-10, '13': 1.4312146184360912e-10, '14': 0.0}

    Step 47 --- T = 46
    Emergy = {'11': 606.2492031229959, '12': 659.9981333360001, '13': 818.7507968769564, '14': 75.00000000000001}
    Empower = {'11': 0.0, '12': 0.0, '13': 0.0, '14': 0.0}

    Step 48 --- T = 47
    Emergy = {'11': 606.2492031229983, '12': 659.9981333360001, '13': 818.7507968769636, '14': 75.00000000000001}
    Empower = {'11': 2.407542772542919e-12, '12': 8.667197317574456e-12, '13': 7.222700544634203e-12, '14': 0.0}

    Step 49 --- T = 48
    Emergy = {'11': 606.2492031230036, '12': 659.9981333360001, '13': 818.7507968769795, '14': 75.00000000000001}
    Empower = {'11': 5.3006358608403755e-12, '12': 1.9082384511902027e-11, '13': 1.5902066603187155e-11, '14': 0.0}

    Step 50 --- T = 49
    Emergy = {'11': 606.2492031230064, '12': 659.9981333360001, '13': 818.7507968769881, '14': 75.00000000000001}
    Empower = {'11': 0.0, '12': 0.0, '13': 0.0, '14': 0.0}
    [Finished in 0.5s]


# Documentation
See http://ecomathique.org/emergylib/
