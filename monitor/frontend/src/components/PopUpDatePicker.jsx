import React, { useState, useEffect } from 'react'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import Modal from 'react-modal'

const PopUpDatePicker = () => {
    const [modalIsOpen, setModalIsOpen] = useState(false)
    const [selectedDate, setSelectedDate] = useState(null)
    const [selectedTime, setSelectedTime] = useState(null)
    const [timeZone, setTimeZone] = useState('')
    const [formattedDateTime, setFormattedDateTime] = useState('')
    const [copyMessageVisible, setCopyMessageVisible] = useState(false)
    const [rawString, setRawString] = useState('')

    const openModal = () => {
        setModalIsOpen(true)
    }

    const closeModal = () => {
        setModalIsOpen(false)
    }

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

    const handleDateChange = (date) => {
        setSelectedDate(date)
        formatDateTime(date, selectedTime, timeZone)
    }

    const handleTimeChange = (time) => {
        setSelectedTime(time)
        formatDateTime(selectedDate, time, timeZone)
    }

    const handleTimeZoneChange = (event) => {
        setTimeZone(event.target.value)
    }

    const handleRawStringChange = (event) => {
        setRawString(event.target.value)
    }

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
            {/* ... (Your existing JSX for rendering the component) */}
            <Modal
                isOpen={modalIsOpen}
                onRequestClose={closeModal}
                style={
                    {
                        // ... (Your existing style for the modal)
                    }
                }
            >
                {/* ... (Your existing JSX for modal content) */}
                <label htmlFor="date">Date:</label>
                <DatePicker
                    id="date"
                    selected={selectedDate}
                    onChange={handleDateChange}
                    dateFormat="y-MM-dd"
                />
                <label htmlFor="time">Time:</label>
                <DatePicker
                    id="time"
                    selected={selectedTime}
                    onChange={handleTimeChange}
                    showTimeSelect
                    showTimeSelectOnly
                    timeIntervals={15}
                    dateFormat="HH:mm"
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
                {/* ... (Your existing JSX for other modal content) */}
            </Modal>
            {/* ... (Your existing JSX for styling) */}
        </div>
    )
}

export default PopUpDatePicker
