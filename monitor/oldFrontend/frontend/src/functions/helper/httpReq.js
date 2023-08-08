const USER = 'nost-client'
const PASS = 'nost-2021'

/**
 * Wrapper for HTTP requests
 *
 * @param {string} url
 * @param {object} body
 * @param {function} send
 * @param {string} type
 * @param {object} defaultValue
 */
const request = (url, body = null, send, type = 'GET', defaultValue = {}) => {
    fetch(url, {
        method: type,
        body: body ? JSON.stringify(body) : undefined,
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: 'Basic ' + btoa(USER + ':' + PASS),
        },
    })
        // .then((res) => res.json())
        .then((response) => {
            send(response)
        })
        .catch((err) => {
            console.log(err)
            send(defaultValue)
        })
}

export default request
