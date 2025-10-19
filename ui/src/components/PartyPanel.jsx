// ui/src/components/PartyPanel.jsx (Definitive Version)

import React from 'react';
import Avatar from './Avatar';

function PartyPanel({ participants, currentUser, isGM, sessionMode, dragPreviewRef }) {
  return (
    <div className="party-panel">
      {participants.map(p => {
        const isDraggable = isGM && sessionMode === 'staging' && p.x_pos === null;
        return (
          <Avatar
            key={p.id}
            participant={p}
            isGM={isGM}
            isSelf={p.player_id === currentUser.id}
            isDraggable={isDraggable}
            // This function's only job is to set the data.
            onAvatarDragStart={(e) => {
              e.dataTransfer.setData("participantId", p.id);
            }}
            dragPreviewRef={dragPreviewRef}
          />
        );
      })}
    </div>
  );
}

export default PartyPanel;