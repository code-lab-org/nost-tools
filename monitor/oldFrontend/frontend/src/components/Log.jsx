import React, { useState, useEffect } from 'react'
import { useMqttState, useSubscription } from 'mqtt-react-hooks'
import * as dayjs from 'dayjs'
import Dropdown from './Dropdown'

/**
 * Displays logs for MQTT messages on the given topic.
 * This component is responsible for visualizing the execution logs of MQTT messages.
 * It subscribes to MQTT topics, receives messages, and filters and displays them accordingly.
 */
const Log = () => {
    // Get the MQTT topic prefix from local storage
    const prefix = localStorage.getItem('prefix')

    // State to hold the number of log messages to display
    const [count, setCount] = useState(200)

    // States to store log messages and their corresponding timestamps
    const [messages, setMessages] = useState(() => {
        // Retrieve messages from local storage or initialize as an empty array
        const storedMessages = localStorage.getItem('logMessages')
        return storedMessages ? JSON.parse(storedMessages) : []
    })
    const [timeMsgs, setTimeMsgs] = useState([])

    // States for managing topics and selected topics
    const [ignore, setIgnore] = useState([])
    const [selected, setSelected] = useState([`${prefix}/#`])
    const [topics, setTopics] = useState([`${prefix}/#`])

    // State to manage the current theme (default or dark)
    const [theme, setTheme] = useState('default')

    // Get the MQTT connection status and received MQTT messages
    const { status } = useMqttState()
    const { msgs } = useSubscription('#')
    const saveLogs = (format) => {
        const filename = `logs-${dayjs().format(
            'YYYY-MM-DD_HH-mm-ss'
        )}.${format}`
        let content

        if (format === 'txt') {
            // Create a plain text representation of the log messages
            content = messages
                .map(
                    (message) =>
                        `${message.time.toISOString().slice(0, -5)} ${
                            message.topic
                        }: ${JSON.stringify(message.message)}`
                )
                .join('\n')
        } else if (format === 'json') {
            // Create a JSON representation of the log messages
            content = JSON.stringify(messages, null, 4)
        }

        // Create a Blob containing the content
        const blob = new Blob([content], { type: `text/${format}` })

        // Create a URL for the Blob
        const url = window.URL.createObjectURL(blob)

        // Create an anchor element to trigger the download
        const a = document.createElement('a')
        a.href = url
        a.download = filename

        // Append the anchor element to the document and click it to trigger the download
        document.body.appendChild(a)
        a.click()

        // Remove the anchor element from the document
        document.body.removeChild(a)
    }

    // Function to toggle between light and dark themes
    const toggleTheme = () => {
        // Toggle the theme between default and dark
        if (theme === 'default') {
            setTheme('dark')
            document.body.style = 'background: #1a1a2e'
            localStorage.setItem('theme', 'dark')
        } else {
            setTheme('default')
            document.body.style = 'background: #fff'
            localStorage.setItem('theme', 'default')
        }
    }

    // Function to change the MQTT topic prefix
    const changePrefix = (newPrefix) => {
        // Update the MQTT topic prefix in local storage
        localStorage.setItem('prefix', newPrefix)

        // Reload the page to apply the new prefix
        window.location.reload(false)
    }

    // Function to update the selected MQTT topics
    const select = (data) => setSelected(data)

    // Effect to handle received MQTT messages and update logs
    useEffect(() => {
        if (status === 'connected' && msgs.length > 0) {
            // Create a new log entry with timestamp for the latest received message
            let timeMessages = timeMsgs
            timeMessages.push({
                ...msgs[msgs.length - 1],
                time: dayjs(),
            })
            setTimeMsgs(timeMessages)

            // Filter and update log messages based on selected topics and count
            let filteredMessages = timeMessages.filter(
                (message) =>
                    !ignore.includes(message.topic) &&
                    !message.topic.includes('-manager/time')
            )

            if (selected.length > 0 && !selected.includes(`${prefix}/#`)) {
                filteredMessages = filteredMessages.filter((message) =>
                    selected.includes(message.topic)
                )
            } else if (selected.includes(`${prefix}/#`)) {
                filteredMessages = filteredMessages.filter((message) =>
                    message.topic.includes(`${prefix}/`)
                )
            }

            setMessages(
                filteredMessages.length > count
                    ? filteredMessages.reverse().slice(0, count)
                    : filteredMessages.reverse()
            )

            // Update the list of available topics for the Dropdown component
            setTopics([
                ...filteredMessages
                    .map((o) => o.topic)
                    .filter((v, i, a) => a.indexOf(v) === i)
                    .filter((topic) => topic.includes(`${prefix}/`)),
                `${prefix}/#`,
            ])
        }
    }, [msgs.length])

    // Effect to update logs when selected topics or ignored topics change
    useEffect(() => {
        // Filter and update log messages based on selected topics and ignored topics
        let filteredMessages = timeMsgs.filter(
            (message) =>
                !ignore.includes(message.topic) &&
                !message.topic.includes('-manager/time')
        )

        if (selected.length > 0 && !selected.includes(`${prefix}/#`)) {
            filteredMessages = filteredMessages.filter((message) =>
                selected.includes(message.topic)
            )
        } else if (selected.includes(`${prefix}/#`)) {
            filteredMessages = filteredMessages.filter((message) =>
                message.topic.includes(`${prefix}/`)
            )
        }

        setMessages(
            filteredMessages.length > count
                ? filteredMessages.reverse().slice(0, count)
                : filteredMessages.reverse()
        )
    }, [selected, ignore])

    // Effect to set the theme from local storage on component mount
    useEffect(() => {
        // Retrieve the theme from local storage and apply it
        const localTheme = localStorage.getItem('theme')
        if (localTheme === 'dark') {
            setTheme('dark')
            document.body.style = 'background: #000'
        }
    }, [])

    // State to manage whether to display messages as formatted JSON or plain text
    const [showJSON, setShowJSON] = useState(false)

    return (
        <div className="logs">
            <div className="logs-header">
                <p>Execution Logs</p>
                {/* Dropdown component to select MQTT topics */}
                <Dropdown
                    topics={topics}
                    select={select}
                    selected={selected}
                    theme={theme}
                />
            </div>
            <div className="logs-console">
                <div className="logs-console-logs">
                    {/* Display each MQTT message as a log item */}
                    {messages?.map((message) => (
                        <div key={message.id} className="logs-message">
                            <p className="logs-message-label">
                                {/* Display timestamp and topic of the message */}
                                {message.time.toISOString().slice(0, -5)}
                                {'   '}
                                {message.topic}
                                <span className="logs-message-label-colon">
                                    :
                                </span>
                            </p>
                            {/* Display the message body, optionally as formatted JSON */}
                            {showJSON ? (
                                <pre className="logs-message-json">
                                    {JSON.stringify(message.message, null, 4)}
                                </pre>
                            ) : (
                                <p className="logs-message-body">
                                    {JSON.stringify(message.message)}
                                </p>
                            )}
                        </div>
                    ))}
                </div>
                <div className="logs-footer">
                    <div className="logs-footer-options">
                        {/* Checkbox to toggle JSON formatting */}
                        <input
                            className="logs-checkbox"
                            type="checkbox"
                            checked={showJSON}
                            onChange={() => setShowJSON(!showJSON)}
                        />
                        <p>Show formatted JSON</p>
                    </div>
                    <div className="logs-footer-export">
                        {/* Placeholder for "Save" functionality */}
                        {/* Text link to save logs as TXT */}
                        {/* Link to save logs as TXT */}
                        <a
                            onClick={() => saveLogs('txt')}
                            style={{ cursor: 'pointer', marginRight: '10px' }}
                        >
                            Save as TXT
                        </a>

                        {/* Link to save logs as JSON */}
                        <a
                            onClick={() => saveLogs('json')}
                            style={{ cursor: 'pointer' }}
                        >
                            Save as JSON
                        </a>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Log
