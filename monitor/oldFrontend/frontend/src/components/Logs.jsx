import React, { useContext, useState, useEffect } from 'react'
import Log from './Log'
import { Context } from '../functions/Provider'
import { v4 as uuidv4 } from 'uuid'

const Logs = () => {
    const { selected, logsCount, view } = useContext(Context)
    const [logs, setLogs] = useState([])

    const generateLogs = (count) => {
        const generatedLogs = Array.from({ length: count }, (_, index) => ({
            id: uuidv4(),
            component: (
                <Log
                    key={uuidv4()}
                    label={`Log ${index + 1}`}
                    selectedTopic={selected}
                />
            ),
        }))
        setLogs(generatedLogs)
    }

    useEffect(() => {
        generateLogs(logsCount)
    }, [logsCount, selected])

    const renderLogs = () => {
        switch (view) {
            case 'infinite':
                return (
                    <div className="logs-console-logs-infinite">
                        {logs.map((log) => (
                            <div key={log.id} className="logs-message-infinite">
                                <div className="logs-message-label">
                                    <span className="logs-message-label-colon">
                                        {log.component.props.label}:{' '}
                                    </span>
                                </div>
                                <div className="logs-message-body-infinite">
                                    {log.component}
                                </div>
                            </div>
                        ))}
                    </div>
                )
            case 'grid':
                return (
                    <div
                        className="logs-console-logs-grid"
                        style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(2, 1fr)',
                            gap: '10px',
                            border: '1px solid transparent',
                        }}
                    >
                        {logs.map((log) => (
                            <div
                                key={log.id}
                                className="logs-message-grid"
                                style={{
                                    boxSizing: 'border-box',
                                    padding: '10px',
                                    border: '1px solid transparent',
                                }}
                            >
                                <div className="logs-message-label">
                                    <span className="logs-message-label-colon">
                                        {log.component.props.label}:{' '}
                                    </span>
                                </div>
                                <div className="logs-message-body-grid">
                                    {log.component}
                                </div>
                            </div>
                        ))}
                    </div>
                )
            default:
                return (
                    <div className="logs-console-logs-infinite">
                        {logs.map((log) => (
                            <div key={log.id} className="logs-message-infinite">
                                <div className="logs-message-label">
                                    <span className="logs-message-label-colon">
                                        {log.component.props.label}:{' '}
                                    </span>
                                </div>
                                <div className="logs-message-body-infinite">
                                    {log.component}
                                </div>
                            </div>
                        ))}
                    </div>
                )
        }
    }

    return (
        <div
            style={{
                height: '100vh',
                display: 'flex',
                flexDirection: 'column',
            }}
        >
            {/* ... (unchanged code) */}
            <div
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '10px', // Add some padding for better display
                }}
            >
                {renderLogs()}
            </div>
            {/* ... (unchanged code) */}
        </div>
    )
}

export default Logs
