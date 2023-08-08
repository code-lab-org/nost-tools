import React, { useContext, useState } from 'react'
import { Context } from '../functions/Provider'

const Settings = () => {
    const {
        theme,
        toggleTheme,
        prefix,
        changePrefix,
        logsCount,
        setLogsCount,
        view,
        setView,
    } = useContext(Context)
    const [input, setInput] = useState(prefix)

    return (
        <div className="settings">
            <div className="settings-header">Functional Configuration</div>
            <div className="settings-row">
                <div
                    className={`settings-button ${
                        prefix !== input ? '' : 'settings-inactive'
                    }`}
                    onClick={() => {
                        if (prefix !== input) {
                            changePrefix(input)
                        }
                    }}
                >
                    Change Prefix
                </div>
                <input
                    className="settings-input"
                    placeholder="Prefix"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                />
            </div>
            <div className="settings-header">Visual</div>
            <div className="settings-row">
                <div className="settings-button" onClick={() => toggleTheme()}>
                    {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                </div>
            </div>
            <div className="settings-header">Logs Configuration</div>
            <div className="settings-row">
                <label htmlFor="logCountInput" className="settings-label">
                    Number of Logs:
                </label>
                <input
                    id="logCountInput"
                    type="number"
                    value={logsCount}
                    onChange={(e) => {
                        const count = parseInt(e.target.value, 10)
                        setLogsCount(count)
                    }}
                    min="1"
                    className="settings-input"
                />
            </div>
            <div className="settings-row">
                <label htmlFor="viewSelect" className="settings-label">
                    Log View:
                </label>
                <select
                    id="viewSelect"
                    value={view}
                    onChange={(e) => {
                        const selectedView = e.target.value
                        if (
                            selectedView === 'grid' ||
                            selectedView === 'infinite'
                        ) {
                            setView(selectedView)
                        }
                    }}
                >
                    <option value="infinite">Infinite Scroll</option>
                    <option value="grid">Grid</option>
                </select>
            </div>
        </div>
    )
}

export default Settings
