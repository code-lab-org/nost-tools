.. _commonInteracts:

Development of Common Internal Application Interactions
========================================================
While the the New Observing Strategies Testbed supports a wide range of test suites, there are certain interactions that will appear frequently regardless of the specifics of the project. 
As in any system, there are key components that form the backbone of the model - connections to the broker, status messages, data transfers, etc. 
Understanding how these common interactions can be used to simplify a new potential model can reduce the amount of time spent designing applications and interactions. 

The first step when preparing a scenario using the NOS Testbed is identifying the components that are necessary, closely followed by identifying their interactions. Once all of the applications are identified, the user must consider how each application will interact with the other applications, external services, and the broker. 
A good method for defining these interactions is to consider if the data transmissions are 'reports', where one application is sending data to another without prompting actions (data downlinks, etc.) or a 'conversation', where two or more applications are delivering data that prompts an action from either the sender or receiver (satellite tasking requests, data processing, state changes, etc.). 
Each of these interaction types (one-way or multi-directional) will have a scenario-dependent structure, but for internal interactions such as application-to-broker, or application-to-application, there are general structural concepts that can be followed to simplify the design process. 

The main group of interactions that will remain consistent across most scenarios are the application/broker interactions. 

In time-managed scenarios, a necessary interaction will be the time status, or 'heartbeat' messages. These messages are crucial for debugging and connectivity management. A standard heartbeat message contains the application's internal time, state variables, and updates on changes in connectivity.
Having a record of these values as a test case progresses allows the user to affirm that all applications are in good standing and functioning as expected, and in the event that they are not, isolate the time and cause of the disconnect.

Internal application-to-application interactions come in many forms depending on the scenario, but in satellite mission modeling, many scenarios will include a data downlink to a ground station. 
Two unique applications, a satellite and a ground station, can be modeled to represent real-world data transmission conditions including capacity, latency, and a field of regard. 
These messages are fundamentally similar to the 'heartbeat' messages - they should contain at minimum the time of downlink and the data being transmitted. 
Downlink messages facilitate the exchange of information between applications, and can be formatted depending on the unique needs of the scenario. 

Although specifics may vary from scenario to scenario, using the documented common interactions can help users build a new model quickly and efficiently. 	