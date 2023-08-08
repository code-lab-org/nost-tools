import React from 'react'
import { useLocation, Link } from 'react-router-dom'

const routes = [
    { name: 'Logs', route: '/logs' },
    { name: 'Overview', route: '/overview' },
    { name: 'Test Script', route: '/testScript' },
    { name: 'Settings', route: '/settings' },
]

/**
 * Navigation bar for application below header
 */
const Navigation = () => {
    const location = useLocation()

    const NavigationItem = ({ name, route }) => {
        return (
            <Link
                className={`navigation-item ${
                    route == location.pathname ? 'navigation-item-current' : ''
                }`}
                to={route}
            >
                {name}
            </Link>
        )
    }

    return (
        <div className="navigation">
            <div className="navigation-content">
                {routes.map((props) => (
                    <NavigationItem {...props} key={props.name} />
                ))}
            </div>
        </div>
    )
}

export default Navigation
