import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { Context } from '../functions/Provider'
import Overview from './Overview'

describe('<Overview />', () => {
    it('renders and initializes correctly', async () => {
        // Mocking fetch function
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: true,
                json: jest.fn(() => Promise.resolve({ success: true })),
            })
        )

        // Mocking context
        const mockContextValue = { prefix: 'testPrefix' }

        render(
            <Context.Provider value={mockContextValue}>
                <Overview />
            </Context.Provider>
        )

        // Simulate input changes
        fireEvent.change(screen.getByPlaceholderText('Sim. Start Time'), {
            target: { value: '100' },
        })
        fireEvent.change(screen.getByPlaceholderText('Sim. Stop Time'), {
            target: { value: '200' },
        })

        // Clicking Initialize button
        fireEvent.click(screen.getByText('Initialize'))

        // Validate that fetch is called with correct parameters
        expect(fetch).toHaveBeenCalledWith('./init/testPrefix', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                simStartTime: '100',
                simStopTime: '200',
                requiredApps: [],
            }),
        })
    })
})
