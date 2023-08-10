// ./src/components/Overview.jsx
// Required imports
import React, { useContext, useState, useEffect } from 'react'
import { Context } from '../functions/Provider'
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

    const [lastCommandStatus, setLastCommandStatus] = useState(null) // To hold the status of the last command
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
        timeScaleFactor2: '', // ...other input fields
    })

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
            )
            const apiErrorsFromLocalStorage = JSON.parse(
                localStorage.getItem('apiErrors') || '[]'
            )
            if (apiErrorsFromLocalStorage.length) {
                setLastCommandStatus({
                    commandLabel,
                    status: 'error',
                    message: 'Failed!',
                })
            } else {
                setLastCommandStatus({
                    commandLabel,
                    status: 'success',
                    message: 'Success!',
                })
            }
        } catch (error) {
            console.error(`${commandLabel} command error:`, error.message)
            setLastCommandStatus({
                commandLabel,
                status: 'error',
                message: 'Error occurred!',
            })
        }

        // Reset message after 6 seconds
        setTimeout(() => {
            setLastCommandStatus(null)
        }, 6000)
    }

    // Handle input changes
    const handleInputChange = (inputName, value) => {
        setInitInputs((prevInputs) => ({ ...prevInputs, [inputName]: value }))
    }

    const formatDate = (value) => {
        let datetime = new Date(value);
        return datetime.toISOString();
    };

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
                                onClick={() =>
                                    handleCommandClick(commandFunction, label)
                                }
                            >
                                {label}
                            </button>

                            <div className="overview-status-message">
                                {lastCommandStatus &&
                                    lastCommandStatus.commandLabel ===
                                        label && (
                                        <div
                                            className={`status-${lastCommandStatus.status}`}
                                        >
                                            {lastCommandStatus.message}
                                        </div>
                                    )}
                            </div>

                            {inputFields.map(
                                ({ label: inputLabel, stateKey }) => (
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
                                                handleInputChange(
                                                    stateKey,
                                                    e.target.value
                                                )
                                            }
                                        />
                                    </div>
                                )
                            )}
                        </div>
                    ))
                }

                <div>
                    
<div className="overview">API Local Logs
                
                
                
                </div>

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

                </div>
                <Nodes />
            </div>

        </div>
    )
}

export default Overview



