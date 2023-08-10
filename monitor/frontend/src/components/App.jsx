import React from 'react'
import { Connector } from 'mqtt-react-hooks'

import { Control } from '../functions/Provider'
import Router from './Router'
import '../styles/style.scss'

const brokerUrl = 'mqtts://testbed.mysmce.com:8443'
const options = {
    protocol: 'mqtts',
    secureProtocol: 'TLS_method',
    username: 'manager',
    password: 'Iy11OBtEq0Zb',
    rejectUnauthorized: false,
    useSSL: false,
    connectionTimeout: 5000,
}

/**
 * App entry point containing:
 *  - MQTT provider
 *  - Control provider
 *  - React router
 */
function App() {
    return (
        <Connector brokerUrl={brokerUrl} opts={options}>
            <Control>
                <Router />
            </Control>
        </Connector>
    )
}

export default App
