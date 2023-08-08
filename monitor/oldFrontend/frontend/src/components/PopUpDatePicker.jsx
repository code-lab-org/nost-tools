import React, { useState, useEffect } from 'react'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import Modal from 'react-modal'

const PopUpDatePicker = () => {
    // State variables
    const [modalIsOpen, setModalIsOpen] = useState(false)
    const [selectedDate, setSelectedDate] = useState(null)
    const [selectedTime, setSelectedTime] = useState(null)
    const [timeZone, setTimeZone] = useState('')
    const [formattedDateTime, setFormattedDateTime] = useState('')
    const [copyMessageVisible, setCopyMessageVisible] = useState(false)
    const [rawString, setRawString] = useState('')

    // Open modal
    const openModal = () => {
        setModalIsOpen(true)
    }

    // Close modal
    const closeModal = () => {
        setModalIsOpen(false)
    }

    // Update selected date, selected time, and time zone based on the raw string
    useEffect(() => {
        if (rawString) {
            const dateTimeParts = rawString.split('T')
            if (dateTimeParts.length === 2) {
                const datePart = dateTimeParts[0]
                const timeAndZonePart = dateTimeParts[1]

                const date = new Date(datePart)
                const timeAndZoneParts = timeAndZonePart.split(timeZone)
                const timePart = timeAndZoneParts[0]

                setSelectedDate(date)
                setSelectedTime(new Date(`1970-01-01T${timePart}`))
            }
        } else {
            setSelectedDate(null)
            setSelectedTime(null)
        }
    }, [rawString, timeZone])

    // Format date and time
    const formatDateTime = (date, time, tz) => {
        if (date && time && tz) {
            const formattedDate = date.toISOString().split('T')[0]
            const formattedTime = time.toISOString().split('T')[1].split('.')[0]
            const rfc3339DateTime = `${formattedDate}T${formattedTime}${tz}`

            setFormattedDateTime(rfc3339DateTime)
            setRawString(rfc3339DateTime)
        } else {
            setFormattedDateTime('')
            setRawString('')
        }
    }

    // Handle date change
    const handleDateChange = (date) => {
        setSelectedDate(date)
        formatDateTime(date, selectedTime, timeZone)
    }

    // Handle time change
    const handleTimeChange = (time) => {
        setSelectedTime(time)
        formatDateTime(selectedDate, time, timeZone)
    }

    // Handle time zone change
    const handleTimeZoneChange = (event) => {
        setTimeZone(event.target.value)
        // formatDateTime(selectedDate, selectedTime, event.target.value)
    }

    // Handle raw string change
    const handleRawStringChange = (event) => {
        setRawString(event.target.value)
    }

    // Handle copy date click
    const handleCopyDateClick = () => {
        if (formattedDateTime) {
            navigator.clipboard.writeText(formattedDateTime)
            setCopyMessageVisible(true)
            setTimeout(() => {
                setCopyMessageVisible(false)
            }, 2000)
        }
    }

    return (
        <div>
            <div className="overview-row">
                <div className="overview-input-container">
                    <input
                        type="text"
                        id="preview"
                        className="overview-input"
                        placeholder="Please enter"
                        value={rawString}
                        onChange={handleRawStringChange}
                    />
                    <button
                        className="overview-button-small"
                        onClick={openModal}
                    >
                        🗓️
                    </button>
                </div>
            </div>

            <Modal
                isOpen={modalIsOpen}
                onRequestClose={closeModal}
                style={{
                    overlay: {
                        backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    },
                    content: {
                        width: '300px',
                        height: '400px',
                        margin: 'auto',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'space-evenly',
                        backgroundColor: '#333',
                        color: '#fff',
                        border: 'none',
                        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
                    },
                }}
            >
                <div className="overview-row">
                    <label htmlFor="preview">Preview:</label>
                    <div className="preview-value">
                        {selectedDate && selectedTime && timeZone ? (
                            <>
                                <span className="date-value">
                                    {selectedDate.toLocaleDateString()}
                                </span>
                                <span className="time-value">
                                    {selectedTime.toLocaleTimeString()}
                                </span>
                                <span className="timezone-value">
                                    {timeZone}
                                </span>
                            </>
                        ) : (
                            ''
                        )}
                    </div>
                </div>
                <label htmlFor="date">Date:</label>
                <DatePicker
                    id="date"
                    selected={selectedDate}
                    onChange={handleDateChange}
                />
                <label htmlFor="time">Time:</label>
                <DatePicker
                    id="time"
                    selected={selectedTime}
                    onChange={handleTimeChange}
                    showTimeSelect
                    showTimeSelectOnly
                    timeIntervals={15}
                    dateFormat="h:mm aa"
                />
                <label htmlFor="timezone">Time Zone:</label>
                <input
                    type="text"
                    id="timezone"
                    placeholder="Enter time zone"
                    value={timeZone}
                    onChange={handleTimeZoneChange}
                    style={{ marginBottom: '10px' }}
                />
                <div className="button-container">
                    <button
                        className="overview-button"
                        onClick={() => {
                            formatDateTime(selectedDate, selectedTime, timeZone)
                            closeModal()
                        }}
                    >
                        Insert
                    </button>
                    <button className="overview-button" onClick={closeModal}>
                        Close
                    </button>
                    <button
                        className="overview-button"
                        onClick={handleCopyDateClick}
                    >
                        Copy
                    </button>
                </div>
                {copyMessageVisible && (
                    <div style={{ marginTop: '10px' }}>
                        Copied RFC-3339 Code
                    </div>
                )}
            </Modal>

            <style jsx>{`
                .overview-button-small {
                    padding: 5px;
                    font-size: 16px;
                    background-color: #f1f1f1;
                    border: none;
                    cursor: pointer;
                    outline: none;
                }

                .overview-button {
                    padding: 10px;
                    font-size: 16px;
                    background-color: #f1f1f1;
                    border: none;
                    cursor: pointer;
                    outline: none;
                    margin-right: 10px;
                }

                .button-container {
                    display: flex;
                    justify-content: center;
                    margin-top: 10px;
                }

                .preview-value {
                    padding: 5px;
                    background-color: #f1f1f1;
                    border-radius: 4px;
                    color: #333;
                    white-space: pre-wrap;
                    word-break: break-word;
                    display: flex;
                    align-items: center;
                }

                .date-value {
                    margin-right: 5px;
                }

                .time-value {
                    margin-right: 5px;
                }

                .timezone-value {
                    margin-left: 5px;
                }
            `}</style>
        </div>
    )
}

export default PopUpDatePicker
