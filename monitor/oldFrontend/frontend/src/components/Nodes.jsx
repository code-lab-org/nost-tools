import React, { useContext, useState } from 'react'
import _ from 'lodash'

import { Context } from '../functions/Provider'
import Modal from './Modal'

/**
 * Displays system applications on Overview component
 */
const Nodes = () => {
    const { nodes } = useContext(Context)
    const [open, setOpen] = useState('')

    return (
        <>
            <div className="nodes-header">
                <p>System Applications</p>
            </div>
            <div className="nodes-list">
                {nodes.map((node) => (
                    <div className="nodes-list-node" key={JSON.stringify(node)}>
                        <div className="nodes-list-node-name">{node.name}</div>
                        <div className="nodes-list-node-desc">
                            {node.description}
                        </div>
                        {_.has(node, 'properties.resource') &&
                            node.properties.resource.slice(0, 4) == 'http' && (
                                <>
                                    <div
                                        onClick={() =>
                                            setOpen(JSON.stringify(node))
                                        }
                                    >
                                        {' '}
                                        Open Resource
                                    </div>
                                    <Modal
                                        title={node.name + ' Resource'}
                                        open={open === JSON.stringify(node)}
                                        close={() => setOpen('')}
                                    >
                                        <iframe
                                            className="modal-iframe"
                                            src={node.properties.resource}
                                        />
                                    </Modal>
                                </>
                            )}
                    </div>
                ))}
            </div>
        </>
    )
}

export default Nodes
