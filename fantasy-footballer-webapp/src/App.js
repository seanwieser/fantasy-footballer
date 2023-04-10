import { BrowserRouter as Router, Routes, Route} from 'react-router-dom';

import './App.css';
import Home from './pages/home/home';
import Members from './pages/members/members';
import Gallery from './pages/gallery/gallery';
import ChatStats from './pages/chatstats/chatstats';
import History from './pages/history/history';



function App(){
  return (
    <div>
      <NavBar/>
      <Router>
        <Routes>
          <Route path='/' exact  element={<Home/>} />
          <Route path='/members' element={<Members/>} />
          <Route path='/gallery' exact  element={<Gallery/>} />
          <Route path='/chatstats' element={<ChatStats/>} />
          <Route path='/history' element={<History/>} />
        </Routes>
      </Router>
    </div>
  );
}

function NavButton(props) {
  function GoToPage() {
      const url_ext = `/${props.text.toLowerCase().replace(" ", "")}`;
      return window.location=url_ext;      
  }
  return <button onClick={GoToPage} className='nav--button' >{props.text}</button>;
}

function NavBar() {

  return (
      <nav className="nav">
          <h3 className='nav--h3'>Sco' Chos</h3>
          <NavButton text='Gallery'/>
          <NavButton text='Members'/>
          <NavButton text='Chat Stats'/>
          <NavButton text='History'/>
      </nav>
  );
}

export default App;
