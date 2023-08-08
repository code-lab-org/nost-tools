import React, { createContext, useState, useEffect } from 'react'
import useControl from './control'

export const Context = createContext()

/**
 * Provider for application functionality
 *
 * @param {component} children
 */
export const Control = ({ children }) => {
    const localPrefix = localStorage.getItem('prefix')
    const savedLogsCount = localStorage.getItem('logsCount')
    const savedView = localStorage.getItem('view')

    // State variables for logsCount and view
    const [logsCount, setLogsCount] = useState(
        savedLogsCount ? parseInt(savedLogsCount, 10) : 1
    )
    const [view, setView] = useState(
        savedView === 'grid' || savedView === 'infinite'
            ? savedView
            : 'infinite'
    )

    const control = useControl(localPrefix)

    // Save logsCount and view to localStorage whenever they change
    useEffect(() => {
        localStorage.setItem('logsCount', logsCount.toString())
    }, [logsCount])

    useEffect(() => {
        localStorage.setItem('view', view)
    }, [view])

    return (
        <Context.Provider
            value={{ ...control, logsCount, setLogsCount, view, setView }}
        >
            {children}
        </Context.Provider>
    )
}
