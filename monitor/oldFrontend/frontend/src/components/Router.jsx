import React, { useContext, useEffect, Suspense, lazy } from 'react'
import { BrowserRouter, Route, Switch, Redirect } from 'react-router-dom'

import Header from './Header'
import StatusHeader from './StatusHeader'
import Navigation from './Navigation'
import Loading from './Loading'
import Footer from './Footer'
import { Context } from '../functions/Provider'

const Overview = lazy(() => import('./Overview'))
const Logs = lazy(() => import('./Logs'))
const TestScript = lazy(() => import('./TestScript'))
const Settings = lazy(() => import('./Settings'))

/**
 * Router allowing for navigation using react-router
 */
const Router = () => {
    const { theme } = useContext(Context)

    useEffect(() => {
        document.body.style.background = theme === 'dark' ? '#1a1a2e' : '#fff'
    }, [theme])

    return (
        <div className={`theme--${theme}`}>
            <div className="main">
                <BrowserRouter>
                    <Header />
                    <StatusHeader />
                    <Navigation />
                    <Suspense fallback={<Loading />}>
                        <Switch>
                            <Route exact path="/loading" component={Loading} />
                            {/* Place the "Logs" route above the "Overview" route */}
                            <Route exact path="/logs" component={Logs} />
                            <Route
                                exact
                                path="/testScript"
                                component={TestScript}
                            />
                            <Route
                                exact
                                path="/settings"
                                component={Settings}
                            />
                            {/* The "Overview" route is defined after the "Logs" route */}
                            <Route
                                exact
                                path="/overview"
                                component={Overview}
                            />
                            <Route
                                path="/"
                                component={() => <Redirect to="/logs" />}
                            />
                        </Switch>
                    </Suspense>
                </BrowserRouter>
                <Footer />
            </div>
        </div>
    )
}

export default Router
