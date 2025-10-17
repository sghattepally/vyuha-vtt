// ui/src/components/ActionPanel.jsx (Corrected)

import React from 'react';

function ActionPanel({ abilities, onSelectMove, onSelectAbility, onEndTurn, isMyTurn, selectedAction, activeParticipant, turnActions = {} }) {
  if (!isMyTurn) {
    return (
      <div className="action-panel">
        <h4>Actions</h4>
        <p>Waiting for another player...</p>
      </div>
    );
  }

  const isDowned = activeParticipant?.status === 'downed';
  const canMove = activeParticipant?.remaining_speed > 0;

  if (isDowned) {
    return (
      <div className="action-panel">
        <h4>Your Turn! (Speed: 0)</h4>
        <p style={{ color: '#ff6b6b', fontWeight: 'bold' }}>You are downed!</p>
        <button className="end-turn-button" onClick={onEndTurn}>End Turn</button>
      </div>
    );
  }

  return (
    <div className="action-panel">
      <h4>Your Turn! (Speed: {activeParticipant?.remaining_speed})</h4>
      <div className="action-buttons">
        <button 
          onClick={onSelectMove} 
          className={selectedAction.type === 'MOVE' ? 'selected' : ''} 
          disabled={!canMove}
        >
          Move
        </button>
        
        {/* --- THIS IS THE FIX --- */}
        {/* Ensure we check that abilities is an array before mapping */}
        {Array.isArray(abilities) && abilities.map(ability => (
          <button 
            key={ability.id} 
            onClick={() => onSelectAbility(ability)} 
            className={selectedAction.ability?.id === ability.id ? 'selected' : ''}
            disabled={turnActions.hasAttacked}
          >
            {ability.name}
          </button>
        ))}
        {/* ----------------------- */}

      </div>
      <button className="end-turn-button" onClick={onEndTurn}>End Turn</button>
    </div>
  );
}

export default ActionPanel;