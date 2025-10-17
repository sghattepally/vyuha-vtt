// ui/src/components/Token.jsx (Corrected)

import React from 'react';

function Token({ participant, isActive, onTokenClick }) {
  // No Hooks are used here, so it is safe.
  const healthPercentage = (participant.current_prana / participant.character.max_prana) * 100;
  const isDowned = participant.status === 'downed';

  const handleClick = () => {
    if (!isDowned && onTokenClick) {
      onTokenClick(participant.id);
    }
  };

  return (
    <div
      className={`token ${isActive ? 'active-token' : ''} ${isDowned ? 'downed' : ''}`}
      onClick={handleClick}
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