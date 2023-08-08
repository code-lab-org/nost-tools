import { useState, useEffect, useMemo } from 'react'
import { useMqttState, useSubscription } from 'mqtt-react-hooks'
import * as dayjs from 'dayjs'

import {
    init,
    start,
    stop,
    update,
    testScript,
    testScriptCancel,
} from './commands'
import { inArray } from './helper/inArray'

/**
 * Hook for application functionality / state management
 *
 * @param {string}
 */
const useControl = (prefix) => {
    const [count, setCount] = useState(200)
    // const [messages, setMessages] = useState([])
    const [timeMsgs, setTimeMsgs] = useState([])
    const [nodes, setNodes] = useState([])
    const [ignore, setIgnore] = useState([])
    // const [selected, setSelected] = useState([`${prefix}/#`])
    // const [topics, setTopics] = useState([`${prefix}/#`])
    const [statusObj, setStatusObj] = useState({
        simTime: '',
        time: '',
        timeScalingFactor: '',
    })
    const [theme, setTheme] = useState('default')
    const [inputs, setInputs] = useState({
        initSimStartTime: '',
        initSimStopTime: '',
        startSimStartTime: '',
        startSimStopTime: '',
        startWallClockStartTime: '',
        startTimeScalingFactor: '',
        startTimeStatusTimeStart: '',
        startPublishStep: '',
        stopSimStopTime: '',
        updateSimUpdateTime: '',
        updateTimeScalingFactor: '',
        testScript: '',
    })

    const { status } = useMqttState()
    const { msgs } = useSubscription('#')

    const toggleTheme = () => {
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

    const changePrefix = (newPrefix) => {
        localStorage.setItem('prefix', newPrefix)

        window.location.reload(false)
    }

    const setRawNodes = (newNodes) => {
        const toAdd = []
        newNodes.forEach((node) => {
            if (!inArray(node, nodes)) {
                toAdd.push(node)
            }
        })
        setNodes([...nodes, ...toAdd])
    }

    // const select = (data) => setSelected(data)

    // useEffect(() => {
    //     if (status == 'connected' && msgs.length > 0) {
    //         // Update status object
    //         if (msgs[msgs.length - 1].topic == `${prefix}/logs/info`) {
    //             setRawNodes([msgs[msgs.length - 1].message])
    //         }

    //         // Add timestamp to each message
    //         let timeMessages = timeMsgs
    //         timeMessages.push({
    //             ...msgs[msgs.length - 1],
    //             time: dayjs(),
    //         })
    //         setTimeMsgs(timeMessages)

    //         // Filter and set message output
    //         if (msgs[msgs.length - 1].topic == `${prefix}-manager/time`) {
    //             setStatusObj(msgs[msgs.length - 1].message.properties)
    //         }

    //         let filteredMessages = timeMessages.filter(
    //             (message) =>
    //                 !ignore.includes(message.topic) &&
    //                 !message.topic.includes('-manager/time')
    //         )
    //         if (selected.length > 0 && !selected.includes(`${prefix}/#`)) {
    //             filteredMessages = filteredMessages.filter((message) =>
    //                 selected.includes(message.topic)
    //             )
    //         } else if (selected.includes(`${prefix}/#`)) {
    //             filteredMessages = filteredMessages.filter((message) =>
    //                 message.topic.includes(`${prefix}/`)
    //             )
    //         }
    //         setMessages(
    //             filteredMessages.length > count
    //                 ? filteredMessages.reverse().slice(0, count)
    //                 : filteredMessages.reverse()
    //         )
    //         setTopics([
    //             ...filteredMessages
    //                 .map((o) => o.topic)
    //                 .filter((v, i, a) => a.indexOf(v) === i)
    //                 .filter((topic) => topic.includes(`${prefix}/`)),
    //             `${prefix}/#`,
    //         ])
    //     }
    // }, [msgs.length])

    // useEffect(() => {
    //     let filteredMessages = timeMsgs.filter(
    //         (message) =>
    //             !ignore.includes(message.topic) &&
    //             !message.topic.includes('-manager/time')
    //     )
    //     if (selected.length > 0 && !selected.includes(`${prefix}/#`)) {
    //         filteredMessages = filteredMessages.filter((message) =>
    //             selected.includes(message.topic)
    //         )
    //     } else if (selected.includes(`${prefix}/#`)) {
    //         filteredMessages = filteredMessages.filter((message) =>
    //             message.topic.includes(`${prefix}/`)
    //         )
    //     }
    //     setMessages(
    //         filteredMessages.length > count
    //             ? filteredMessages.reverse().slice(0, count)
    //             : filteredMessages.reverse()
    //     )
    // }, [selected, ignore])

    useEffect(() => {
        const localTheme = localStorage.getItem('theme')

        if (localTheme == 'dark') {
            setTheme('dark')
            document.body.style = 'background: #000'
        }
    }, [])

    // Bulky boilderplate for performance reasons
    const control = useMemo(
        () => ({
            prefix,
            changePrefix,
            count,
            setCount,
            status,
            // messages,
            theme,
            toggleTheme,
            statusObj,
            nodes,
            init,
            start,
            stop,
            update,
            testScript,
            testScriptCancel,
            // select,
            // selected,
            // topics,
            inputs,
            setInputs,
        }),
        [
            prefix,
            changePrefix,
            count,
            setCount,
            status,
            // messages,
            theme,
            toggleTheme,
            statusObj,
            nodes,
            init,
            start,
            stop,
            update,
            testScript,
            testScriptCancel,
            // select,
            // selected,
            // topics,
            inputs,
            setInputs,
        ]
    )

    return control
}

export default useControl
