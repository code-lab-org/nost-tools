// import request from './helper/httpReq'

// const baseUrl = 'http://127.0.0.1:8000/'

// // 'http://127.0.0.1:8000/' ||
// // 'https://testbed-manager.mysmce.com/api/' ||
// // process.env.BACKEND_URL

// // ./helper/command.js
// /**
//  * Backend request for initializing execution
//  *
//  * @param {string} prefix
//  * @param {string} simStartTime (ISO-8601)
//  * @param {string} simStopTime (ISO-8601)
//  */
// export const init = (prefix, simStartTime, simStopTime) => {
//     request(
//         `${baseUrl}init/${prefix}`,
//         {
//             simStartTime,
//             simStopTime,
//             requiredApps: [],
//         },
//         console.log,
//         'POST'
//     )
// }

// /**
//  * Backend request for starting execution
//  *
//  * @param {string} prefix
//  * @param {number} timeScalingFactor
//  * @param {string} simStartTime (ISO-8601)
//  * @param {string} simStopTime (ISO-8601)
//  * @param {string} startTime (ISO-8601)
//  * @param {string} timeStatusStartTime (ISO-8601)
//  * @param {number} publishStep
//  */
// export const start = (
//     prefix,
//     timeScalingFactor = undefined,
//     simStartTime = undefined,
//     simStopTime = undefined,
//     startTime = undefined,
//     timeStatusStartTime = undefined,
//     publishStep = undefined
// ) => {
//     request(
//         `${baseUrl}start/${prefix}`,
//         {
//             timeScalingFactor: timeScalingFactor
//                 ? parseFloat(timeScalingFactor)
//                 : undefined,
//             simStartTime,
//             simStopTime,
//             startTime: startTime === '' ? undefined : startTime,
//             timeStatusStartTime:
//                 timeStatusStartTime === '' ? undefined : timeStatusStartTime,
//             publishStep:
//                 publishStep === '' ? undefined : parseFloat(publishStep),
//         },
//         console.log,
//         'POST'
//     )
// }

// /**
//  * Backend request for updating execution
//  *
//  * @param {string} prefix
//  * @param {number} timeScalingFactor
//  * @param {string} simUpdateTime (ISO-8601)
//  */
// export const update = (
//     prefix,
//     timeScalingFactor = undefined,
//     simUpdateTime = undefined
// ) => {
//     request(
//         `${baseUrl}update/${prefix}`,
//         {
//             timeScalingFactor,
//             simUpdateTime,
//         },
//         console.log,
//         'POST'
//     )
// }

// /**
//  * Backend request for stopping execution
//  *
//  * @param {string} prefix
//  * @param {string} simStopTime (ISO-8601)
//  */
// export const stop = (prefix, simStopTime = undefined) => {
//     request(
//         `${baseUrl}stop/${prefix}`,
//         {
//             simStopTime,
//         },
//         console.log,
//         'POST'
//     )
// }

// /**
//  * Backend request for test script execution
//  *
//  * @param {string} prefix
//  * @param {object} body
//  */
// export const testScript = (prefix, body) => {
//     request(`${baseUrl}testScript/${prefix}`, body, console.log, 'POST')
// }

// /**
//  * Backend request for cancelling test script execution
//  *
//  * @param {string} prefix
//  */
// export const testScriptCancel = (prefix) => {
//     request(
//         `${baseUrl}testScriptCancel/${prefix}`,
//         undefined,
//         console.log,
//         'GET'
//     )
// }
