/**
 * Helper function to determine whether an object is an array
 *
 * @param {object} obj
 * @param {array} list
 */
export function inArray(obj, list) {
    let i
    for (i = 0; i < list.length; i++) {
        if (JSON.stringify(list[i]) == JSON.stringify(obj)) {
            return true
        }
    }
    return false
}
