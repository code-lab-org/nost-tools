NOS Testbed (NOS-T) Documentation
=================================

The New Observing Strategies Testbed (NOS-T) is a comprehensive digital engineering environment
designed to develop, test, mature, and socialize new operating concepts and technology for
NASA's New Observing Strategies initiative. NOS-T provides a framework for scientists, engineers,
and mission planners to model, simulate, and analyze novel observational approaches across various
space science disciplines.

Key Capabilities
---------------

* **Distributed Simulation Framework**: Connect multiple simulation components through standardized Advanced Message Queuing Protocol (AMQP) messaging protocols
* **Managed Application Architecture**: Synchronize and control simulation components with built-in time management and state control
* **Schema-Based Communication**: Leverage standardized message schemas for consistent data exchange between applications
* **Flexible Deployment Options**: Run simulations locally or deploy to cloud environments like AWS
* **Example Test Suites**: Build on existing scenarios like FireSat+, Science Event Dashboard, and Snow Observing Systems
* **Scalability Testing**: Validate performance under varying message loads and simulation complexities
* **Visualization & Analysis Tools**: Visualize simulation results through integrated dashboards and analysis tools

Who Should Use NOS-T?
--------------------

* Scientists developing new observation strategies for space missions
* Engineers designing spacecraft systems and instruments
* Mission planners optimizing science return and resource utilization
* Researchers evaluating observation trade-offs and capabilities
* Program managers assessing technology readiness and performance metrics

Getting Started
-------------

New to NOS-T? We recommend:

1. Read the :doc:`overview/index` to understand NOS-T fundamentals
2. Follow the :doc:`installation/index` guide to set up your environment
3. Work through tutorials in :doc:`learning_resources/index`
4. Explore :doc:`examples/index` to see NOS-T in action

.. graphviz::
   :name: nos_t_concept
   :caption: NOS-T Graphical Concept: Visual representation of the testbed architecture and operational flow
   :align: center

   digraph NOST_concept {
      // splines=curved;
      // overlap=false;
      
      subgraph cluster0 {
         style=dashed;
         label="User System";
         labeljust="l";
         fontsize=18;
         fontname="Helvetica-Bold";
         
         PI1 [label="NOS PI", shape=rect, style=filled, fillcolor=red];
         PI2 [label="NOS PI", shape=rect, style=filled, fillcolor=blue];
         PI3 [label="NOS PI", shape=rect, style=filled, fillcolor=green];
         UserApp1 [label="User App", shape=rect, style=filled, fillcolor=red];
         UserApp2 [label="User App", shape=rect, style=filled, fillcolor=blue];
         UserApp3 [label="User App", shape=rect, style=filled, fillcolor=green];
      }
      
      TestCase [label="NOS Test Case", shape=oval]
      TestCase -> PI1;
      TestCase -> PI2;
      TestCase -> PI3;
      
      PI1 -> UserApp1;
      PI2 -> UserApp2;
      PI3 -> UserApp3;
      
      subgraph cluster1 {
         style=dashed;
         label="NOS-T System";
         labeljust="l";
         fontsize=18;
         fontname="Helvetica-Bold";
         
         NOSTInfrastructure [label="NOST Infrastructure", style=filled, fillcolor=orange];
         
         subgraph cluster2 {
               style=dashed;
               color=grey;
               labeljust="l";
               fontsize=10;
               label="NOS-T Operator";
               
               EventBroker [label="Event Broker\n(AMQP Protocol)"]
               Fill [style=invis]
               ManagerApplication [label="Manager Application"]
         }
      }
      
      UserApp1 -> NOSTInfrastructure
      UserApp2 -> NOSTInfrastructure
      UserApp3 -> NOSTInfrastructure
      
      NOSTInfrastructure -> EventBroker
      NOSTInfrastructure -> Fill [style=invis]
      NOSTInfrastructure -> ManagerApplication
   
   }


Support and Community
-------------------

* Report issues on our `GitHub repository <https://github.com/code-lab-org/nost-tools/issues>`_
* Attend virtual workshops and training sessions
* Contact the NOS-T team:
   * PI: Paul T. Grogan, `paul.grogan@asu.edu <mailto:paul.grogan@asu.edu>`_
   * Research Scientist: Emmanuel M. Gonzalez, `emmanuelgonzalez@asu.edu <mailto:emmanuelgonzalez@asu.edu>`_

Indices and References
--------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. toctree::
   :hidden:

   overview/index
   installation/installation
   learning_resources/index
   operators_guide/index
   nost_tools_api/index
   examples/index
   resources_library/index
   release_docs/index
   publications
   contributing/index
   faq/index