import React, { useContext, useState } from 'react'
import { Context } from '../functions/Provider'
import PopUpDatePicker from './PopUpDatePicker'

import Nodes from './Nodes'

import {
    runInitCommand,
    runStartCommand,
    runStopCommand,
    runUpdateCommand,
    // runTestScript,
} from '../functions/api.js'

const Overview = () => {
    const { prefix } = useContext(Context)
    const [initInputs, setInitInputs] = useState({
        initSimStartTime: '',
        initSimStopTime: '',
        startSimStartTime: '',
        startSimStopTime: '',
        wallclockStartTime: '',
        timeScaleFactor: '',
        timeStatusStartTime: '',
        publishStep: '',
        stopSimStopTime: '',
        updateSimUpdateTime: '',
        timeScaleFactor: '',
    })

    const handleCommandClick = async (commandFunction, commandLabel) => {
        try {
          const responseData = await commandFunction(
            prefix,
            initInputs.initSimStartTime,
            initInputs.initSimStopTime
          );
    
          const log = `${commandLabel} command successful with prefix: ${prefix}\nResponse Data: ${JSON.stringify(
            responseData
          )}`;
    
          logMessage(log);
          alert(log);
        } catch (error) {
          const errorMessage = `${commandLabel} command error: ${error.message}`;
          logMessage(errorMessage);
          alert(errorMessage);
        }
      };

    const handleInputChange = (inputName, value) => {
        setInitInputs((prevInputs) => ({ ...prevInputs, [inputName]: value }))
    }

    return (
        <div className="overview">
            <div className="overview-header">Commands</div>
            <div className="overview-buttons">
                {[
                    {
                        label: 'Initialize',
                        commandFunction: runInitCommand,
                        inputFields: [
                            {
                                label: 'Simulation Start Time',
                                stateKey: 'initSimStartTime',
                            },
                            {
                                label: 'Simulation Stop Time',
                                stateKey: 'initSimStopTime',
                            },
                        ],
                    },
                    {
                        label: 'Start',
                        commandFunction: runStartCommand,
                        inputFields: [
                            {
                                label: 'Simulation Start Time',
                                stateKey: 'startSimStartTime',
                            },
                            {
                                label: 'Simulation Stop Time',
                                stateKey: 'startSimStopTime',
                            },
                            {
                                label: 'Wallclock Start Time',
                                stateKey: 'wallclockStartTime',
                            },
                            {
                                label: 'Time Scale Factor (sec)',
                                stateKey: 'timeScaleFactor',
                            },
                            {
                                label: 'Time Status Start Time',
                                stateKey: 'timeStatusStartTime',
                            },
                            {
                                label: 'Publish Step (sec)',
                                stateKey: 'publishStep',
                            },
                        ],
                    },
                    {
                        label: 'Stop',
                        commandFunction: runStopCommand,
                        inputFields: [
                            {
                                label: 'Simulation Stop Time',
                                stateKey: 'stopSimStopTime',
                            },
                        ],
                    },
                    {
                        label: 'Update',
                        commandFunction: runUpdateCommand,
                        inputFields: [
                            {
                                label: 'Simulation Update Time',
                                stateKey: 'updateSimUpdateTime',
                            },
                            {
                                label: 'Time Scale Factor (sec) ',
                                stateKey: 'timeScaleFactor',
                            },
                        ],
                    },
                ].map(({ label, commandFunction, inputFields }) => (
                    <div className="overview-row" key={label}>
                        <button
                            className="overview-button"
                            onClick={() => handleCommandClick(commandFunction)}
                        >
                            {label}
                        </button>
                        {/* Input fields for commands */}
                        {inputFields.map(({ label, stateKey }) => (
                            <input
                                key={label}
                                className="overview-input"
                                placeholder={label}
                                value={initInputs[stateKey]}
                                onChange={(e) =>
                                    handleInputChange(stateKey, e.target.value)
                                }
                            />
                        ))}
                    </div>
                ))}

                <Nodes />
            </div>
        </div>
    )
}

export default Overview
