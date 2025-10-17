// ui/src/components/InitiativeTracker.jsx (Corrected)

import React from 'react';

function InitiativeTracker({ participants, turnOrder, currentTurnIndex }) {
  // A safety check in case the data isn't ready yet
  if (!turnOrder || turnOrder.length === 0) {
    return (
        <div className="initiative-tracker">
            <h3>Turn Order</h3>
            <p>Waiting for initiative...</p>
        </div>
    );
  }
  
  // Create a map for quick lookups
  const participantMap = new Map(participants.map(p => [p.id, p]));
  const activeParticipantId = turnOrder[currentTurnIndex];

  return (
    <div className="initiative-tracker">
      <h3>Turn Order</h3>
      <ol>
        {turnOrder.map(participantId => {
          const participant = participantMap.get(participantId);
          if (!participant) return null; // Safety check for missing participant data

          return (
            <li key={participant.id} className={participant.id === activeParticipantId ? 'active-turn' : ''}>
              {/* --- THIS IS THE NEW DISPLAY LOGIC --- */}
              {participant.character.name} 
              <span className="hp-tracker">
                ({participant.current_prana}/{participant.character.max_prana})
              </span>
              {/* ------------------------------------ */}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export default InitiativeTracker;