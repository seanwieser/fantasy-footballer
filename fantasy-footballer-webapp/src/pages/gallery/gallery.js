import './gallery.css';
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


function Gallery() {
    return (
        <div>
            <RandomPlayer />            
        </div>
    )
}

export default Gallery;