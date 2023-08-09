// api.js

const BASE_URL = 'http://127.0.0.1:8000/'

export async function callApi(endpoint, method, data = {}) {
    console.log(
        `callApi - Endpoint: ${endpoint}, Method: ${method}, Data:`,
        data
    )

    const url = `${BASE_URL}${endpoint}`
    const headers = {
        'Content-Type': 'application/json',
        Accept: 'application/json',
    }

    const options = {
        method,
        headers,
        body: JSON.stringify(data),
    }

    try {
        const response = await fetch(url, options)

        if (!response.ok) {
            const textResponse = await response.text()
            const errorMessage = `Error: ${textResponse}`
            console.error(errorMessage)
            throw new Error(errorMessage)
        }

        const responseData = await response.json()
        return responseData
    } catch (error) {
        const fetchErrorMessage = `Fetch error: ${error.message}`
        console.error(fetchErrorMessage)
        throw new Error(fetchErrorMessage)
    }
}

export async function getStatus(testName) {
    console.log(`getStatus - Test Name: ${testName}`)

    const endpoint = `status/${testName}`
    return await callApi(endpoint, 'GET')
}

export async function runInitCommand(testName, simStartTime, simStopTime) {
    console.log(
        `runInitCommand - Test Name: ${testName}, Sim Start Time: ${simStartTime}, Sim Stop Time: ${simStopTime}`
    )

    const endpoint = `init/${testName}`
    const data = {
        simStartTime,
        simStopTime,
        requiredApps: [],
    }
    return await callApi(endpoint, 'POST', data)
}

export async function runStartCommand(testName, simStartTime, simStopTime) {
    const endpoint = `start/${testName}`
    const data = {
        simStartTime,
        simStopTime,
        startTime: simStartTime, // Update this according to your needs
        timeStep: 1,
        timeScaleFactor: 1,
        timeStatusStep: 0,
        timeStatusInit: simStartTime, // Update this according to your needs
    }
    return await callApi(endpoint, 'POST', data)
}

export async function runStopCommand(testName, simStopTime) {
    const endpoint = `stop/${testName}`
    const data = {
        simStopTime,
    }
    return await callApi(endpoint, 'POST', data)
}

export async function runUpdateCommand(
    testName,
    simUpdateTime,
    timeScaleFactor
) {
    const endpoint = `update/${testName}`
    const data = {
        timeScaleFactor,
        simUpdateTime,
    }
    return await callApi(endpoint, 'POST', data)
}

// You can add more functions for additional API calls if needed
