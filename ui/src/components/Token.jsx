// ui/src/components/Token.jsx
import React from 'react';

function Token({ participant, isActive, onTokenClick }) {
  const healthPercentage = (participant.current_prana / participant.character.max_prana) * 100;
  const isDowned = participant.status === 'downed';

  return (
    <div
      className={`token ${isActive ? 'active-token' : ''} ${isDowned ? 'downed' : ''}`}
      onClick={() => !isDowned && onTokenClick && onTokenClick(participant.id)}
    >
      {participant.character.name.charAt(0)}
      {!isDowned && (
        <div className="health-bar-background">
          <div className="health-bar-foreground" style={{ width: `${healthPercentage}%` }}></div>
        </div>
      )}
    </div>
  );
}
export default Token;