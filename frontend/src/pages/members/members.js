import './members.css';
import {useState, useEffect}  from 'react';
import axios from 'axios';
import '@fontsource/roboto/300.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';
import { FormControl, Select, InputLabel, MenuItem } from '@mui/material';


function MemberByYear() {
    const [members, setMembers] = useState([])
    const [year, setYear] = useState("2022")

    const years = ["2018", "2019", "2020", "2021", "2022"]
    const menuItems = years.map((year, index) => {
        return <MenuItem key={index} value={year}>{year}</MenuItem>
    })
    const memberList = members.map((member, index) => {
        return <p key={index}>{member}</p>
    })

    useEffect(() => {
        axios.get(`/members/${year}`)
            .then(res => setMembers(res.data))
    }, [year])

    const handleChange = event => {
        setYear(event.target.value)
    }

   return (
    <div>
        <FormControl fullWidth>
            <InputLabel id="demo-simple-select-label">Year</InputLabel>
            <Select
                labelId="demo-simple-select-label"
                id="demo-simple-select"
                value={year}
                label="Year"
                onChange={handleChange}
            >
                {menuItems}
            </Select>
        </FormControl>
        {memberList}
    </div>)

}


function Members() {
    return (
        <div>
            <MemberByYear />            
        </div>
    )
}

export default Members;