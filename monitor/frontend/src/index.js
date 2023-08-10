import React from 'react'
import ReactDOM from 'react-dom'

import App from './components/App'

window.Buffer = window.Buffer || require('buffer').Buffer
global.Buffer = global.Buffer || require('buffer').Buffer

ReactDOM.render(<App />, document.getElementById('app'))
