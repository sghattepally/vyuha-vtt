// ui/src/App.jsx

import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css'; // We'll keep the basic styling for now

function App() {
  // 1. STATE: This is where React will "remember" our game session data.
  // We start with `null` because we haven't loaded anything yet.
  const [sessionData, setSessionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 2. EFFECT: This code runs ONCE, when the component first loads.
  // It's the perfect place to fetch our initial data.
  useEffect(() => {
    // We define an async function to make the API call
    const fetchSessionData = async () => {
      try {
        // Make a GET request to our FastAPI backend to load session #1
        const response = await axios.get('http://localhost:8000/sessions/1/');
        
        // Store the data we received in our state
        setSessionData(response.data);
      } catch (err) {
        // If something goes wrong, store the error message
        setError('Failed to load game session. Is the backend server running?');
        console.error(err);
      } finally {
        // No matter what, stop the loading indicator
        setLoading(false);
      }
    };

    fetchSessionData(); // Call the function to start fetching
  }, []); // The empty array [] means "only run this effect once"

  // 3. RENDER LOGIC: This decides what to show on the screen.
  if (loading) {
    return <div>Loading Game...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>{error}</div>;
  }

  // 4. THE UI: If loading is done and there's no error, show the game data!
  return (
    <div className="game-room">
      <h1>Vyuha VTT</h1>
      <h2>Campaign: {sessionData.campaign_name}</h2>
      <div className="session-status">
        <p><strong>Mode:</strong> {sessionData.current_mode}</p>
        <p><strong>Loka Resonance:</strong> {sessionData.active_loka_resonance}</p>
      </div>

      <h3>Participants</h3>
      <div className="participants-grid">
        {sessionData.participants.map((participant) => (
          <div key={participant.id} className="character-card">
            <h4>{participant.character_name}</h4>
            <p><strong>Prāṇa:</strong> {participant.current_prana}</p>
            <p><strong>Tapas:</strong> {participant.current_tapas}</p>
            <p><strong>Māyā:</strong> {participant.current_maya}</p>
            <p><strong>Position:</strong> ({participant.x_pos}, {participant.y_pos})</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;