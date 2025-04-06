import { Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import LiveFeed from './components/LiveFeed';

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/livefeed" element={<LiveFeed />} />
    </Routes>
  );
}

export default App;
