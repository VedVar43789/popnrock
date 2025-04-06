import { Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import LiveFeed from './components/LiveFeed';
import FERPage from './components/FERpage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/livefeed" element={<LiveFeed />} />
      <Route path="/fer" element={<FERPage />} />
    </Routes>
  );
}

export default App;