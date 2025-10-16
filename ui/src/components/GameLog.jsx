// ui/src/components/GameLog.jsx
import React from 'react';

function GameLog({ messages }) {
  return (
    <div className="game-log">
      <h4>Game Log</h4>
      {messages.map((msg, index) => (
        <p key={index} className={`log-message ${msg.startsWith('Error:') ? 'error' : ''}`}>{msg}</p>
      ))}
    </div>
  );
}
export default GameLog;