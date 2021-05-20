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

# Documentation
See http://ecomathique.org/emergylib/
