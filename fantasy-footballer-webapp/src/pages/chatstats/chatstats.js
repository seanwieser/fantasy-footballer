import './chatstats.css';
import sampleData from '../../data/sampleData';
import React from 'react';


function RandomPlayer() {
    const [playerIdx, setPlayerName] = React.useState(0)

    function clickHandler() {
        setPlayerName(prevIdx => {
            return (prevIdx+1)%3
        })
    }


    return <button onClick={clickHandler}>{sampleData[playerIdx].player}</button>
}


function ChatStats() {
    return (
        <div>
            <RandomPlayer />   
            ChatStats         
        </div>
    )
}

export default ChatStats;