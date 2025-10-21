// ui/src/components/Avatar.jsx (Corrected)

import React, { useState, useRef } from 'react';
import ReactDOM from 'react-dom';
import ResourceDots from './ResourceDots';

const getModifier = (score) => {
  const modifier = Math.floor((score - 10) / 2);
  return modifier >= 0 ? `+${modifier}` : `${modifier}`;
};

const Tooltip = ({ participant, isSelf, isGM, position }) => {
  if (!position) return null;
  const { character, status, current_prana, current_tapas, current_maya } = participant;
  const style = { position: 'fixed', top: position.top, left: position.left, transform: position.transform, zIndex: 1000 };

  return ReactDOM.createPortal(
    <div className="avatar-tooltip" style={style}>
      <h4>{character.name}</h4>
      {/* --- FIX IS HERE --- */}
      <p>{character.race.name} {character.char_class.name}, Level {character.level}</p>
      <p>Status: <span className="status-text">{status}</span></p>
      <hr />
      <div className="tooltip-resources">
        <p><strong>Prāṇa:</strong> {current_prana} / {character.max_prana}</p>
        <p><strong>Tapas:</strong> {current_tapas} / {character.max_tapas}</p>
        <p><strong>Māyā:</strong> {current_maya} / {character.max_maya}</p>
      </div>
      <hr />
      {(isGM || isSelf) && (
        <div className="tooltip-stats">
          <p><strong>Bala:</strong> {character.bala} ({getModifier(character.bala)})</p>
          <p><strong>Dakṣatā:</strong> {character.dakshata} ({getModifier(character.dakshata)})</p>
          <p><strong>Dhṛti:</strong> {character.dhriti} ({getModifier(character.dhriti)})</p>
          <p><strong>Buddhi:</strong> {character.buddhi} ({getModifier(character.buddhi)})</p>
          <p><strong>Prajñā:</strong> {character.prajna} ({getModifier(character.prajna)})</p>
          <p><strong>Saṃkalpa:</strong> {character.samkalpa} ({getModifier(character.samkalpa)})</p>
        </div>
      )}
    </div>,
    document.getElementById('tooltip-root')
  );
};

function Avatar({ participant, isSelf, isGM, isDraggable, onAvatarDragStart, dragPreviewRef }) {
  const { character, current_prana, current_tapas, current_maya, status } = participant;
  const initials = character.name.substring(0, 2).toUpperCase();
  const avatarRef = useRef(null);
  const [tooltipPosition, setTooltipPosition] = useState(null);

  const handleMouseEnter = () => { if (avatarRef.current) {
    const rect = avatarRef.current.getBoundingClientRect();
    const tooltipWidth = 240;
    let left = rect.left + rect.width / 2;
      let transform = 'translateX(-50%)'; // Default: center the tooltip

      // Check if it's going off the right edge of the screen
      if (left + (tooltipWidth / 2) > window.innerWidth) {
        left = rect.right;
        transform = 'translateX(-100%)'; // Align right edge of tooltip with right edge of avatar
      }

      // Check if it's going off the left edge of the screen
      if (left - (tooltipWidth / 2) < 0) {
        left = rect.left;
        transform = 'translateX(0%)'; // Align left edge of tooltip with left edge of avatar
      }

      setTooltipPosition({
        left: left,
        top: rect.bottom + 10,
        transform: transform,
      });
     } };
  const handleMouseLeave = () => setTooltipPosition(null);

  const handleDragStart = (e) => {
    onAvatarDragStart(e);
    if (dragPreviewRef.current) {
      e.dataTransfer.setDragImage(dragPreviewRef.current, 25, 25);
    }
  };

  return (
    <div
      className={`avatar-container ${isSelf ? 'is-self' : ''}`}
      ref={avatarRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      draggable={isDraggable}
      onDragStart={handleDragStart}
    >
      <div className="avatar-circle">{initials}{status !== 'active' && <div className="status-effect-icon">{status.charAt(0).toUpperCase()}</div>}</div>
      <div className="avatar-info">
        <span className="avatar-name">{character.name}</span>
        <div className="resource-display">
          {/* Prāṇa can remain a bar for now, or you can convert it too if you like */}
          <div
            className="prana-bar"
            title={`Prāṇa: ${current_prana} / ${character.max_prana}`}
          >
            <div
              className="prana-bar-fill"
              style={{ width: `${(current_prana / character.max_prana) * 100}%` }}
            ></div>
          </div>
          <ResourceDots
            current={current_tapas}
            max={character.max_tapas}
            color="#ff9800"
            resourceName="Tapas"
          />
          <ResourceDots
            current={current_maya}
            max={character.max_maya}
            color="#2196f3"
            resourceName="Māyā"
          />
        </div>
      </div>
      <Tooltip participant={participant} isSelf={isSelf} isGM={isGM} position={tooltipPosition} />
    </div>
  );
}

export default Avatar;