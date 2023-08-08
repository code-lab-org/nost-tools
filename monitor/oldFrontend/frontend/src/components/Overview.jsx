import React, { useContext } from 'react'
import { Context } from '../functions/Provider'
import PopUpDatePicker from './PopUpDatePicker'
import Nodes from './Nodes'

/**
 * Shows GUI commands for controlling backend state
 */
const Overview = () => {
    const { prefix, init, start, stop, update, inputs, setInputs } =
        useContext(Context)

    return (
        <div className="overview">
            <div className="overview-header">Commands</div>
            <div className="overview-buttons">
                <div className="overview-row">
                    <div
                        className="overview-button"
                        onClick={() =>
                            init(
                                prefix,
                                inputs.initSimStartTime,
                                inputs.initSimStopTime
                            )
                        }
                    >
                        Initialize
                    </div>
                    <input
                        className="overview-input"
                        placeholder="Sim. Start Time"
                        value={inputs.initSimStartTime}
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                initSimStartTime: e.target.value,
                            })
                        }
                    />
                    <input
                        className="overview-input"
                        placeholder="Sim. Stop Time"
                        value={inputs.initSimStopTime}
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                initSimStopTime: e.target.value,
                            })
                        }
                    />
                </div>
                <div className="overview-row" style={{ marginBottom: 5 }}>
                    <div
                        className="overview-button"
                        onClick={() =>
                            start(
                                prefix,
                                inputs.startTimeScalingFactor,
                                inputs.startSimStartTime,
                                inputs.startSimStopTime,
                                inputs.startWallClockStartTime,
                                inputs.timeStatusStartTime,
                                inputs.publishStep
                            )
                        }
                    >
                        Start
                    </div>
                    <input
                        className="overview-input"
                        placeholder="Sim. Start Time"
                        value={inputs.startSimStartTime}
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                startSimStartTime: e.target.value,
                            })
                        }
                    />
                    <input
                        className="overview-input"
                        placeholder="Sim. Stop Time"
                        value={inputs.startSimStopTime}
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                startSimStopTime: e.target.value,
                            })
                        }
                    />
                    <input
                        className="overview-input"
                        placeholder="Wallclock Start Time"
                        value={inputs.startWallclockStartTime}
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                startWallclockStartTime: e.target.value,
                            })
                        }
                    />
                </div>
                <div className="overview-row">
                    <div className="overview-button-filler" />
                    <input
                        className="overview-input"
                        placeholder="Time Scale Factor (seconds)"
                        value={inputs.startTimeScalingFactor}
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                startTimeScalingFactor: e.target.value,
                            })
                        }
                    />
                    <input
                        className="overview-input"
                        placeholder="Time Status Start Time"
                        value={inputs.timeStatusStartTime}
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                timeStatusStartTime: e.target.value,
                            })
                        }
                    />
                    <input
                        className="overview-input"
                        placeholder="Publish Step (seconds)"
                        value={inputs.publishStep}
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                publishStep: e.target.value,
                            })
                        }
                    />
                </div>
                <div className="overview-row">
                    <div
                        className="overview-button"
                        onClick={() => stop(prefix, inputs.stopSimStopTime)}
                    >
                        Stop
                    </div>
                    <input
                        className="overview-input"
                        placeholder="Sim. Stop Time"
                        value={inputs.stopSimStopTime}
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                stopSimStopTime: e.target.value,
                            })
                        }
                    />
                </div>
                <div className="overview-row">
                    <div
                        className="overview-button"
                        onClick={() =>
                            update(
                                prefix,
                                inputs.updateTimeScalingFactor,
                                inputs.updateSimUpdateTime
                            )
                        }
                    >
                        Update
                    </div>
                    <input
                        className="overview-input"
                        placeholder="Sim. Update Time"
                        value={inputs.updateSimUpdateTime}
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                updateSimUpdateTime: e.target.value,
                            })
                        }
                    />
                    <input
                        className="overview-input"
                        placeholder="Time Scale Factor (seconds)"
                        onChange={(e) =>
                            setInputs({
                                ...inputs,
                                updateTimeScalingFactor: e.target.value,
                            })
                        }
                    />
                </div>
            </div>
            <PopUpDatePicker placeholder="Time Status Start Time" />
            <Nodes />
        </div>
    )
}

export default Overview
