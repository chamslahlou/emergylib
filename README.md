# emergylib
A python library for computing emergy

# Authors
Chams Lahlou, Olivier Le Corre and Laurent Truffet


# Overview

This library allows to:

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

    network.run_steady_state(source_flow, tank_flow, tank_load, is_operational, display=True)

compute emergy and empower of products in real-time:

    network.run_scenario('sim_data.txt','results.txt', display=True)

# Installation

1. Install Python 3 if necessary.

2. Install Cython if necessary.

3. Download emergy package.

4. Unzip the package


Compile cython module by:

    python setup-ugraph.py build_ext --inplace

# Documentation
See http://ecomathique.org/emergylib/
