Status Messages
===============

When the connectivity of an individual application must be monitored, 
or the status of an application must be known for an event trigger, a 'heartbeat'
message is utilized to provide regular, timestamped updates for an application's 
connection to the broker. 


..
    To ask brian:
..
    need to add image for the heartbeat messages

.. 
    need to add example schema in here as well, maybe master doc of all schemas?

..
    need to add link to use case in example firesat

Description
---------------------
The 'heartbeat' connection is a series of messages passed between an application
and the manager to inform the manager and other relevant applications of it's connectivity
status. As seen in the image, the message sequence begins with connectivity status updates,
and upon successful connection, the application begins to issue the 'heatbeat', which affirms
connectivity and provides useful status information along with a timestamp (locations for satellites, coordinates for ground stations, etc.).
When the application shuts down, whether intentionally or accidentally, the termination sequence begins and messages are issued 
relaying the disconnection to the manager. 
