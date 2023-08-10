import React from 'react'
import Spinner from 'react-spinkit'

/**
 * Loading component for application transitions
 *
 * @param {number} height
 * @param {number} width
 */
const Loading = (props) => {
    const { height, width } = props
    return (
        <div
            style={{
                position: 'absolute',
                left: '50%',
                top: '50%',
                transform: 'translate(-50%, -50%)',
                height: height || 75,
                width: width || 75,
            }}
        >
            <Spinner
                name="double-bounce"
                color="#eee"
                style={{ height: height || 75, width: width || 75 }}
            />
        </div>
    )
}

export default Loading
