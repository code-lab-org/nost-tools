.. _commonIssues:

Common Technical Issues
=======================

This section contains some common technical issues the development team encountered along with methods for overcoming them. Please click on the dropdown menus.

.. dropdown:: Why can't I connect to the broker?

    If you are having trouble connecting with the broker there are several possible causes. Not having the proper credentials to log in is a likely cause. Depending on how your organization handles these credentials, one of these would be if your IP address is not recognized by the broker host. Make sure that your broker administrator has your IP address on a whitelist. Relatedly, if you generally connect to the use a VPN make sure that it's turned on. You might see a ``timeout: timed out`` error message if your VPN is not turned on.
  
.. dropdown:: Why can't I see my messages being published?

    If you are not able to see an application's messages publishing to the broker, the first step is to ensure that the application can connect to the broker. See the question above for guidance on broker connection issues. If the application is correctly connected, next verify that the topic the application is publishing to is the desired channel. Furthermore, make sure you are monitoring the desired channel if you are using the online manager. For event-driven applications, validate that the trigger event is occuring, and the application in question is receiving the trigger as needed. If the application is connected to the appropriate channel and receiving the trigger, validate the syntax of the message -- if there is a syntax error, the message will not populate correctly. 

.. dropdown:: Do I need to use the NOS-T manager?

    You do not need to use the NOS-T manager. However, many if not most applications which require scaled time (i.e. a faster-than-real-time simulation) will want to use it. Some test suites, like :ref:`FireSat+ <fireSatExampleTop>`, have both managed and unmanaged applications working together. A more in-depth description of these distinctions is found :ref:`here <unmgdVSmgd>`.

.. dropdown:: Can I run duplicate applications?

    Yes, you can duplicate applications to create copies of various nodes. However, in some cases duplicating applications might not be necessary or desirable. Some clear examples of this would be if you want to use multiple spacecraft or ground stations as opposed to one. Your applications can be developed so that, for instance, a constellation of spacecraft is represented by one application, rather than requiring applications for each individual spacecraft. The :ref:`FireSat+ <fireSatExampleTop>` **Grounds** application has a simple example of this. In the below config.py code block, the top commented lines could be used to represent 7 separate ground stations. The bottom lines which aren't commented are used to represent a single ground station. Using a single application to represent several nodes will cut down on message traffic - this will prevent slowdown during test cases.

    .. code-block:: python

        GROUND = pd.DataFrame(
            # data={
            #     "groundId": [0, 1, 2, 3, 4, 5, 6],
            #     "latitude": [35.0, 30.0, -5.0, -30.0, 52.0, -20.0, 75.0],
            #     "longitude": [-102.0, -9.0, -60.0, 25.0, 65.0, 140.0, -40.0],
            #     "elevAngle": [5.0, 15.0, 5.0, 10.0, 5.0, 25.0, 15.0],
            #     "operational": [True, True, True, True, True, False, False],
            # }
            data={
                "groundId": [0],
                "latitude": [LAT],
                "longitude": [LNG],
                "elevAngle": [MIN_ELEVATION],
                "operational": [True],
            }
        )

.. dropdown:: Why aren't my visualizations populating?

    When generating science dashboards or simulation models, first validate the port number is correct.
    Next, validate that the data is importing correctly: for satellites, ensure all TLEs are updated and in appropriate format,
    and for graphs, ensure data sources are accurate and in the correct format.

    Also, most visualization tools should be started up before they start receiving data. For visualization tools receiving data from a managed application, the manager should be started last.

.. dropdown:: Why doesn't my managed application start up?

    This is commonly caused by the NOS-T manager starting up before the managed application. Sometimes, even if you start up the manager last, delays in initializing the managed application can cause timing problems. The initialization process is described :ref:`here <controlEvents>`. In particular, repeated NTP requests on the managed application can delay the startup enough so that the manager sends out its initialization messages before the application is ready. In the case of the :ref:`FireSat+ <fireSatExampleTop>` example applications, you should wait until you see the following message in your IDE console

    .. code-block:: 

        INFO:nost_tools.application:Contacting pool.ntp.org to retrieve wallclock offset.
        INFO:nost_tools.application:Wallclock offset updated to 0:00:00.248738.
        INFO:nost_tools.application:Application ground successfully started up.

.. dropdown:: Do all my applications need to be hosted on one device?

    No! One of the benefits of using the NOS-T architecture is that applications can be hosted throughout a distrubuted network, so long as each machine can be connected to the broker.

.. dropdown:: How can I map my complex scenario into an NOS-T project?

    The first step in evaluating a project for modeling with NOS-T is to break down components of the scenario into individual components that can be turned into applications. Once these applications are identified, determine the way they will interact. Common interactions and methods for determining them are detailed in the whitepaper :ref:`commonInteracts`.

.. dropdown:: How do I fix a pydantic error?

    If you receive a pydantic error similar to the one below:

    .. code-block::
    
        pydantic.error_wrappers.ValidationError: 1 validation error for SatelliteStatus position 
        value is not a valid list (type=type_error.list)

    Then you are probably sending out a message that does not have the correct data type. Check the data type for that element in the message (SatelliteStatus position above) and make sure that it is of the correct data type (list in the example above). These schema are very helpful for catching these data type errors.


    





