// ui/src/components/CombatGrid.jsx (Definitive Fix)

import React from 'react';
import Token from './Token';
import MovementOverlay from './MovementOverlay';

const GRID_CELL_SIZE = 50;

function CombatGrid({ participants, isGM, onTokenMove, onGridClick, onTokenClick, activeParticipantId, showMovementFor }) {
  
  const handleDragOver = (e) => e.preventDefault();
  
  const handleDrop = (e) => {
    e.preventDefault();
    if (!isGM || !onTokenMove) return;
    const participantId = parseInt(e.dataTransfer.getData("participantId"));
    if (!participantId) return;
    const gridRect = e.currentTarget.getBoundingClientRect();
    const gridX = Math.floor((e.clientX - gridRect.left) / GRID_CELL_SIZE);
    const gridY = Math.floor((e.clientY - gridRect.top) / GRID_CELL_SIZE);
    onTokenMove(participantId, gridX, gridY);
  };

  const handleGridClick = (e) => {
    // This ensures clicks on tokens don't count as grid clicks
    if (e.target === e.currentTarget && onGridClick) {
      const gridRect = e.currentTarget.getBoundingClientRect();
      const gridX = Math.floor((e.clientX - gridRect.left) / GRID_CELL_SIZE);
      const gridY = Math.floor((e.clientY - gridRect.top) / GRID_CELL_SIZE);
      onGridClick(gridX, gridY);
    }
  };

  return (
    <div 
      className="grid-container" // Use .grid-container from your CSS
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleGridClick}
    >
      {/* This correctly renders the movement overlay when needed */}
      {showMovementFor && <MovementOverlay originX={showMovementFor.x_pos} originY={showMovementFor.y_pos} speed={showMovementFor.remaining_speed} />}

      {participants.map(p => (
        (p.x_pos !== null && p.y_pos !== null) && (
          <div
            key={p.id}
            className="token-container"
            style={{
              left: `${p.x_pos * GRID_CELL_SIZE}px`,
              top: `${p.y_pos * GRID_CELL_SIZE}px`,
            }}
            draggable={!!(isGM && onTokenMove)} 
            onDragStart={(e) => e.dataTransfer.setData("participantId", String(p.id))}
            
          >
            <Token 
              participant={p} 
              isActive={p.id === activeParticipantId}
              onTokenClick={onTokenClick}
            />
          </div>
        )
      ))}
    </div>
  );
}

export default CombatGrid;