import React from 'react'

/**
 * Modal for external resources displayed in init message
 *
 * @param {string} title
 * @param {boolean} open
 * @param {function} close
 * @param {HTMLElement} children
 */
const Modal = ({ title, open, close, children }) => {
    return (
        open && (
            <div className="modal-background">
                <div className="modal-container">
                    <div className="modal-header">
                        <a>{title}</a>
                        <a className="modal-header-exit" onClick={close}>
                            Exit
                        </a>
                    </div>
                    <div className="modal-body">{children}</div>
                </div>
            </div>
        )
    )
}

export default Modal
