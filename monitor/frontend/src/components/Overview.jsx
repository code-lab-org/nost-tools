// ./src/components/Overview.jsx
// Required imports
import React, { useContext, useState, useEffect } from 'react'
import { Context } from '../functions/Provider'
import PopUpDatePicker from './PopUpDatePicker'
import JsonDisplay from './JsonDisplay'
import Nodes from './Nodes'
import {
    runInitCommand,
    runStartCommand,
    runStopCommand,
    runUpdateCommand,
    clearApiLog,
    saveApiLogToFile,
} from '../functions/api.js'

const Overview = () => {
    // Retrieve prefix from context
    const { prefix } = useContext(Context)

    // State declarations
    const [apiLog, setApiLogs] = useState([]) // To hold API logs
    const [lastCommandStatus, setLastCommandStatus] = useState(null)

    const [initInputs, setInitInputs] = useState({
        // To hold initialization inputs
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
        timeScaleFactor: '', // ...other input fields
    })
    const [rerenderTrigger, setRerenderTrigger] = useState(0)

    // Function to generate a JSON display
    const generateJsonDisplay = (jsonData) => {
        return <JsonDisplay data={jsonData} />
    }

    // Effect hook to generate JSON display whenever initInputs changes
    useEffect(() => {
        generateJsonDisplay(initInputs)
    }, [initInputs])

    // Effect hook to get API logs from local storage when the component mounts
    useEffect(() => {
        const storedApiLog = localStorage.getItem('apiLog')
        if (storedApiLog) {
            setApiLogs(JSON.parse(storedApiLog))
        }
    }, [])

    // Effect hook to store the updated apiLog in local storage
    useEffect(() => {
        localStorage.setItem('apiLog', JSON.stringify(apiLog))
    }, [apiLog])

    // Handle API command clicks
    const handleCommandClick = async (commandFunction, commandLabel) => {
        try {
            await commandFunction(
                prefix,
                initInputs.initSimStartTime,
                initInputs.initSimStopTime
            );
    
            setLastCommandStatus({
                status: 'success',
                message: `${commandLabel} command was successful.`,
                commandLabel: commandLabel
            });
    
        } catch (error) {
            console.error(`${commandLabel} command error:`, error.message);
            setLastCommandStatus({
                status: 'error',
                message: `${commandLabel} command encountered an error: ${error.message}.`,
                commandLabel: commandLabel
            });
        }
    
        // Clear the message after 5 seconds
        setTimeout(() => {
            if (lastCommandStatus && lastCommandStatus.commandLabel === commandLabel) {
                setLastCommandStatus(null); 
            }
        }, 5000);
    }
    
    
    

    // Handle input changes
    const handleInputChange = (inputName, value) => {
        setInitInputs((prevInputs) => ({ ...prevInputs, [inputName]: value }))
    }

    // Render
    return (
        <div className="overview">
            <div className="overview-header">Commands</div>
            <div className="overview-buttons">
                {
                    // Mapping commands to render them along with their input fields
                    [
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
                                onClick={() => handleCommandClick(commandFunction, label)}
                            >
                                {label}
                            </button>
                    
                            <div className="overview-status-message">
                                {lastCommandStatus && lastCommandStatus.commandLabel === label && (
                                    <div className={`status-${lastCommandStatus.status}`}>
                                        {lastCommandStatus.message}
                                    </div>
                                )}
                            </div>
                    
                            {inputFields.map(({ label: inputLabel, stateKey }) => (
                                <div
                                    key={inputLabel}
                                    style={{
                                        marginBottom: '10px',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                    }}
                                >
                                    <label
                                        style={{
                                            fontWeight: 'bold',
                                            textAlign: 'center',
                                        }}
                                    >
                                        {inputLabel}
                                    </label>
                                    <input
                                        className="overview-input"
                                        placeholder={inputLabel}
                                        value={initInputs[stateKey]}
                                        onChange={(e) =>
                                            handleInputChange(stateKey, e.target.value)
                                        }
                                    />
                                </div>
                            ))}
                        </div>
                    ))
                }

                <div>
                    <p></p>
                </div>
                <div className="overview-header">API Local Logs</div>

                <div>
                    <div>
                        !!!_NOTICE_!!!: Refresh Page to see latest local logs
                        for api !!!_NOTICE_!!!: click roots to expand
                    </div>
                    {generateJsonDisplay(apiLog)}

                    <div>
                        <button
                            className="overview-button"
                            onClick={() => clearApiLog()}
                        >
                            Clear Log
                        </button>

                        <button
                            className="overview-button"
                            onClick={() => saveApiLogToFile()}
                        >
                            Save Log
                        </button>
                    </div>
                </div>

                <Nodes />
            </div>
        </div>
    )
}

export default Overview
