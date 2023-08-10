// api.js
const BASE_URL = 'http://127.0.0.1:8000/'

// Define a variable to store the API log
let apiLog = []

// Function to add an entry to the API log
function addToApiLog(entry) {
    apiLog.unshift(entry) // Use unshift to add new entries at the beginning
    localStorage.setItem('apiLog', JSON.stringify(apiLog))
}
// clears log from local storage
function clearApiLog() {
    apiLog = [] // Clear the array
    localStorage.removeItem('apiLog') // Remove from local storage
}

// Function to save the API log as a JSON file
function saveApiLogToFile() {
    const fileName = 'apiLog.json'
    const jsonContent = JSON.stringify(apiLog, null, 2)
    const blob = new Blob([jsonContent], { type: 'application/json' })

    // Create a download link
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = fileName
    link.click()

    // Clean up
    URL.revokeObjectURL(link.href)
}
export async function callApi(endpoint, method, data = {}) {
    const timestamp = new Date().toISOString()

    const logEntry = {
        timestamp,
        endpoint,
        method,
        data,
        result: null,
        error: null,
    }

    try {
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

        const response = await fetch(url, options)

        if (!response.ok) {
            const textResponse = await response.text()
            const errorMessage = `Error: ${textResponse}`
            console.error(errorMessage)
            logEntry.error = errorMessage
        } else {
            const responseData = await response.json()
            logEntry.result = responseData
        }
    } catch (error) {
        const fetchErrorMessage = `Fetch error: ${error.message}`
        console.error(fetchErrorMessage)
        logEntry.error = fetchErrorMessage
    } finally {
        addToApiLog(logEntry)
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

// You can also initialize the API log from local storage if it exists
const storedApiLog = localStorage.getItem('apiLog')
if (storedApiLog) {
    apiLog = JSON.parse(storedApiLog)
}

export {
    // callApi,
    // getStatus,
    // runInitCommand,
    // runStartCommand,
    // runStopCommand,
    // runUpdateCommand,
    clearApiLog, // Export the clear function
    saveApiLogToFile, // Export the save function
}
