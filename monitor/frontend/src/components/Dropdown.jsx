import React from 'react'
import { RiArrowDropDownLine as DropDown } from 'react-icons/ri'
import Select from 'react-select'
import makeAnimated from 'react-select/animated'

const animatedComponents = makeAnimated()

const DropdownIndicator = () => <DropDown className="logs-drop-down-icon" />

const IndicatorSeparator = () => null

// Define the function at the module level
const getOptionLabel = (item) => item

const Dropdown = (props) => {
    const { topics, select, selected, theme } = props

    const colorStyles = {
        control: (styles) => ({
            ...styles,
            border: 0,
            boxShadow: 'none',
            highlight: 'none',
            minWidth: 150,
            height: 14,
            marginBottom: 16,
            backgroundColor: 'none',
        }),
        option: (styles) => ({
            ...styles,
        }),
        input: (styles) => ({ ...styles }),
        placeholder: (styles) => ({
            ...styles,
            color: theme === 'dark' ? '#8fa9ce' : '#62738d',
        }),
        singleValue: (styles) => ({
            ...styles,
            color: theme === 'dark' ? '#8fa9ce' : '#62738d',
        }),
        menu: (styles) => ({
            ...styles,
            marginTop: -14,
            backgroundColor: theme === 'dark' ? '#1a1a2e' : '#fff',
        }),
    }

    const components = {
        ...animatedComponents,
        DropdownIndicator: DropdownIndicator,
        IndicatorSeparator: IndicatorSeparator,
    }

    return (
        <Select
            className="logs-drop-down"
            closeMenuOnSelect={false}
            defaultValue={selected}
            isMulti
            options={topics}
            placeholder="Select Topics..."
            onChange={select}
            getOptionLabel={getOptionLabel} // Reference the function directly
            components={components}
            styles={colorStyles}
        />
    )
}

export default Dropdown
