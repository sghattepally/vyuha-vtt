// ui/src/App.jsx (Definitive Fix)

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import GameRoom from './components/GameRoom';
import HomePage from './components/HomePage';
import Lobby from './components/Lobby';
import Token from './components/Token';
import './App.css';

function App() {
  // We only need state for the core data. The UI will be derived from this.
  const [sessionData, setSessionData] = useState(null);
  const [playerData, setPlayerData] = useState(null);
  const [isGmOverride, setIsGmOverride] = useState(false);
  const [error, setError] = useState('');
  const dragPreviewRef = useRef(null);
  const [newLogTrigger, setNewLogTrigger] = useState(0);

  // Effect #1: Load initial state from localStorage on startup.
  useEffect(() => {
    const savedSession = localStorage.getItem('vyuhaSession');
    const savedPlayer = localStorage.getItem('vyuhaPlayer');
    if (savedSession && savedPlayer) {
      setSessionData(JSON.parse(savedSession));
      setPlayerData(JSON.parse(savedPlayer));
    }
  }, []); // Runs only once.
  const handleClearLocalStorage = () => {
      localStorage.clear();
      window.location.reload();
  };
  // Effect #2: Manage the WebSocket connection. Its ONLY job is to update sessionData.
  useEffect(() => {
    // Don't connect until we have the necessary IDs.
    if (!sessionData?.id || !playerData?.id) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionData.id}/${playerData.id}`);
    ws.onopen = () => console.log("WebSocket Connected!");
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'session_update') {
      setSessionData(message.data);
      localStorage.setItem('vyuhaSession', JSON.stringify(message.data));
    } else if (message.type === 'new_log_entry') {
      setNewLogTrigger(prev => prev + 1);
    }
  };
    ws.onerror = (err) => console.error("WebSocket Error:", err);
    ws.onclose = () => console.log("WebSocket Closed.");

    return () => ws.close();
  }, [sessionData?.id, playerData?.id]); // Reconnects only if the session/player fundamentally changes.

  // --- HANDLER FUNCTIONS ---
  // These functions now ONLY handle API calls and update the state. They no longer control the view.
  const handleCreateSession = async (campaignName, gmDisplayName, gmAccessCode) => {
    try {
      const gmUserRes = await axios.post('http://localhost:8000/users/', { display_name: gmDisplayName });
      const gm = gmUserRes.data;
      const sessionRes = await axios.post('http://localhost:8000/sessions', {
        campaign_name: campaignName,
        gm_id: gm.id,
        gm_access_code: gmAccessCode
      });
      const session = sessionRes.data;
      
      // Update our state. The render logic below will automatically show the lobby.
      setPlayerData(gm);
      setSessionData(session);
      localStorage.setItem('vyuhaPlayer', JSON.stringify(gm));
      localStorage.setItem('vyuhaSession', JSON.stringify(session));
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to create session.';
      setError(errorMsg);
    }
  };

  const handleJoinSession = async (accessCode, displayName) => {
    try {
      const response = await axios.post('http://localhost:8000/join', { access_code: accessCode, display_name: displayName });
      const { player, session } = response.data;
      
      // Update our state. The render logic below will automatically show the lobby.
      setPlayerData(player);
      setSessionData(session);
      localStorage.setItem('vyuhaPlayer', JSON.stringify(player));
      localStorage.setItem('vyuhaSession', JSON.stringify(session));
    } catch (err) {
      setError('Failed to join session. Check the code and try again.');
    }
  };

  // --- RENDER LOGIC ---
  // This is the new, robust state machine. It derives the view directly from the data.
  if (!sessionData || !playerData) {
    // If we have no session data, we must be on the home page.
    return <HomePage onCreateSession={handleCreateSession} onJoinSession={handleJoinSession} error={error} />;
  }

  if (sessionData.current_mode === 'lobby') {
    // If the session mode is 'lobby', show the lobby.
    return <Lobby sessionData={sessionData} playerData={playerData} newLogTrigger={newLogTrigger}/>;
  }

  if (['exploration', 'staging', 'combat'].includes(sessionData.current_mode)) {
    // If the mode is any of the in-game modes, show the game room.
    const isGM = playerData.id === sessionData.gm_id;
    return (
      <>
        <div className="gm-toggle">
          <button onClick={handleClearLocalStorage} className="clear-storage-btn" title="Clear Local Storage & Refresh">
            🗑️
          </button>
          <label>
            <input 
              type="checkbox" 
              checked={isGmOverride} 
              onChange={() => setIsGmOverride(prev => !prev)} 
            />
            GM View
          </label>
        </div>
        <div ref={dragPreviewRef} style={{ position: 'fixed', top: '-100px', left: '-100px' }}>
            <div style={{width: '50px', height: '50px'}}>
                <Token participant={{ character: { name: ' ' }, current_prana: 1, max_prana: 1 }} />
            </div>
        </div>
        <GameRoom 
          sessionData={sessionData} 
          currentUser={playerData} 
          isGM={isGM}
          dragPreviewRef={dragPreviewRef}
          isGmOverride={isGmOverride} 
          newLogTrigger={newLogTrigger}
        />
      </>
    );
  }

  // Fallback for any unknown state
  return <div>Loading...</div>;
}

export default App;