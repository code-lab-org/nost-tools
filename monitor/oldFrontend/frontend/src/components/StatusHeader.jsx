import React, { useContext } from 'react'

import { Context } from '../functions/Provider'

/**
 * Header displaying execution state
 */
const StatusHeader = () => {
    const { prefix, statusObj } = useContext(Context)

    return (
        <div className="status-header">
            <div className="status-header-content">
                {statusObj.simTime == '' ? (
                    <div className="status-header-not-running">
                        Simulation Not Running
                    </div>
                ) : (
                    <div className="status-header-state">
                        <div className="status-header-field">
                            <p className="status-header-bold">
                                Simulation Time:
                            </p>
                            <p>{statusObj.simTime.slice(0, 19)}</p>
                        </div>
                        <div className="status-header-field">
                            <p className="status-header-bold">
                                Time Scaling Factor:
                            </p>
                            <p>{statusObj.timeScalingFactor}</p>
                        </div>
                    </div>
                )}
                <div className="status-header-prefix">
                    <p className="status-header-bold">Prefix: </p>
                    <p>{prefix}/#</p>
                </div>
            </div>
        </div>
    )
}

export default StatusHeader
