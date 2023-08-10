import React, { useContext, useState } from 'react'
import axios from 'axios' // assuming you're using axios for HTTP requests
import { Context } from '../functions/Provider'
import PopUpDatePicker from './PopUpDatePicker'

const Controls = () => {
    const { prefix } = useContext(Context)
    const [inputs, setInputs] = useState({
        initSimStartTime: '',
        initSimStopTime: '',
    })

    const init = async (prefix, startTime, stopTime) => {
        try {
            const response = await axios.post(`/init/${prefix}`, {
                simStartTime: startTime,
                simStopTime: stopTime,
                requiredApps: [], // this is hardcoded, change as needed
            })
            console.log(response.data)
        } catch (error) {
            console.error('Error initializing', error)
        }
    }

    return (
        <div className="Controls">
            <div className="Controls-header">Commands</div>
            <div className="Controls-buttons">
                <div className="Controls-row">
                    <div
                        className="Controls-button"
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
                    {/* Example usage of PopUpDatePicker. Adjust as needed. */}
                    <PopUpDatePicker
                        value={inputs.initSimStartTime}
                        onChange={(date) =>
                            setInputs({
                                ...inputs,
                                initSimStartTime: date,
                            })
                        }
                        placeholder="Sim. Start Time"
                    />
                    <PopUpDatePicker
                        value={inputs.initSimStopTime}
                        onChange={(date) =>
                            setInputs({
                                ...inputs,
                                initSimStopTime: date,
                            })
                        }
                        placeholder="Sim. Stop Time"
                    />
                </div>
            </div>
        </div>
    )
}

export default Controls
