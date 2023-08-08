import React, { useContext, useState } from 'react'

import { Context } from '../functions/Provider'
import Modal from './Modal'
import exampleTestScript from '../functions/helper/exampleTestScript'

/**
 * GUI for inputting a test script
 */
const TestScript = () => {
    const { prefix, testScript, testScriptCancel, inputs, setInputs } =
        useContext(Context)
    const [open, setOpen] = useState(false)

    return (
        <div className="test-script">
            <Modal
                title="Example Test Script"
                open={open}
                close={() => setOpen(false)}
            >
                <pre>{JSON.stringify(exampleTestScript, null, 4)}</pre>
            </Modal>
            <div className="test-script-header">
                <p>Test Script Input</p>
                <a
                    className="test-script-example"
                    onClick={() => setOpen(true)}
                >
                    See Example
                </a>
            </div>
            <div className="test-script-input-container">
                <textarea
                    className="test-script-input"
                    value={inputs.testScript}
                    onChange={(e) =>
                        setInputs({ ...inputs, testScript: e.target.value })
                    }
                />
                <div className="test-script-footer">
                    <div
                        className="button-cancel"
                        onClick={() => testScriptCancel(prefix)}
                    >
                        <a>Cancel</a>
                    </div>
                    <div
                        className="button"
                        onClick={() =>
                            testScript(prefix, JSON.parse(inputs.testScript))
                        }
                    >
                        <a>Submit</a>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default TestScript
