import React, { useContext, useState } from 'react'
import Headroom from 'react-headroom'

import { Context } from '../functions/Provider'

/**
 * Dynamic header for entire application, displays MQTT connection status
 */
const Header = () => {
    const { status } = useContext(Context)
    const [show, setShow] = useState(false)

    return (
        <Headroom
            className={show ? '' : 'shadow'}
            onPin={() => setShow(true)}
            onUnfix={() => setShow(false)}
        >
            <div className="header">
                <div className="header-logo">
                    <div className="header-text">🚀 NOS-T</div>
                </div>
                <div className={`header-status status-${status}`}>{status}</div>
            </div>
            <div className="header-gradient" />
        </Headroom>
    )
}

export default Header
