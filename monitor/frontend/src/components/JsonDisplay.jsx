import React from 'react'
import JSONView from 'react-json-view'

const JsonDisplay = ({ data }) => {
    return (
        <div className="json-display">
            <JSONView src={data} theme="rjv-default" collapsed={2} />
        </div>
    )
}

export default JsonDisplay
