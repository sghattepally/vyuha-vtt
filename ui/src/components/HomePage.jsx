// ui/src/components/HomePage.jsx

import React, { useState } from 'react';

function HomePage({ onCreateSession, onJoinSession, error }) {
  const [isCreating, setIsCreating] = useState(false);
  const [campaignName, setCampaignName] = useState('');
  const [gmName, setGmName] = useState('');
  const [gmAccessCode, setGmAccessCode] = useState('');
  const [accessCode, setAccessCode] = useState('');
  const [playerName, setPlayerName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isCreating) {
      onCreateSession(campaignName, gmName, gmAccessCode);
    } else {
      onJoinSession(accessCode, playerName);
    }
  };

  return (
    <div className="home-page">
      <h1>Welcome to Vyuha</h1>
      <div className="form-toggle">
        <button onClick={() => setIsCreating(false)} className={!isCreating ? 'active' : ''}>Join Game</button>
        <button onClick={() => setIsCreating(true)} className={isCreating ? 'active' : ''}>Create Game</button>
      </div>
      <form onSubmit={handleSubmit} className="home-form">
        {isCreating ? (
          <>
            <h2>Create a New Session</h2>
            <input type="text" value={gmName} onChange={(e) => setGmName(e.target.value)} placeholder="Your GM Name" required />
            <input type="text" value={campaignName} onChange={(e) => setCampaignName(e.target.value)} placeholder="Campaign Name" required />
            <input type="password" value={gmAccessCode} onChange={(e) => setGmAccessCode(e.target.value)} placeholder="GM Access Code" required />
          </>
        ) : (
          <>
            <h2>Join an Existing Session</h2>
            <input type="text" value={playerName} onChange={(e) => setPlayerName(e.target.value)} placeholder="Your Display Name" required />
            <input type="text" value={accessCode} onChange={(e) => setAccessCode(e.target.value.toUpperCase())} placeholder="Access Code" required />
          </>
        )}
        <button type="submit">{isCreating ? 'Create' : 'Join'}</button>
      </form>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
}

export default HomePage;