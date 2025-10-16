// ui/src/components/InitiativeTracker.jsx
import React from 'react';

function InitiativeTracker({ participants, turnOrder, currentTurnIndex }) {
  const sortedParticipants = turnOrder.map(participantId => 
    participants.find(p => p.id === participantId)
  );
  
  // A safety check in case the data isn't ready yet
  if (!turnOrder || turnOrder.length === 0) {
    return (
        <div className="initiative-tracker">
            <h3>Turn Order</h3>
            <p>Waiting for initiative...</p>
        </div>
    );
  }

  const activeParticipantId = turnOrder[currentTurnIndex];

  return (
    <div className="initiative-tracker">
      <h3>Turn Order</h3>
      <ol>
        {sortedParticipants.map(participant => (
          participant && ( // Another safety check
            <li key={participant.id} className={participant.id === activeParticipantId ? 'active-turn' : ''}>
              {participant.character.name}
            </li>
          )
        ))}
      </ol>
    </div>
  );
}

export default InitiativeTracker;