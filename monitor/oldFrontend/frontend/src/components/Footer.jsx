import React from 'react'

const baseUrl =
    process.env.BACKEND_URL || 'https://testbed-manager.mysmce.com/api/'

/**
 * Static footer for entire application
 */
const Footer = () => {
    return (
        <div className="footer">
            <div className="footer-info">
                <a className="footer-text" href="https://code-lab.org/">
                    code-lab.org
                </a>
                <a className="footer-text" href={`${baseUrl}docs/index.html`}>
                    Documentation
                </a>
            </div>
            <a className="button" href="mailto:hdaly1@stevens.edu">
                Contact
            </a>
        </div>
    )
}

export default Footer
