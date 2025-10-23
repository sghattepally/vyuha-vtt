import React, { useState } from 'react';

function GiveItemPlayerModal({ currentCharacter, otherParticipants, invItem, onGive, onClose }) {
  const [targetCharId, setTargetCharId] = useState(otherParticipants[0]?.character.id || '');
  const [quantity, setQuantity] = useState(1);
  const showSlider = invItem.item.is_stackable && invItem.quantity > 1;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (targetCharId) {
      onGive(parseInt(targetCharId), parseInt(quantity));
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal give-item-modal">
        <h4>Give "{invItem.item.puranic_name}" to...</h4>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <select value={targetCharId} onChange={(e) => setTargetCharId(e.target.value)}>
              {otherParticipants.map(p => (
                <option key={p.character.id} value={p.character.id}>
                  {p.character.name}
                </option>
              ))}
            </select>
          </div>
          {showSlider && (
            <div className="form-group">
              <label>Quantity: {quantity} ({invItem.quantity}) </label>
              <input
                type="range"
                min="1"
                max={invItem.quantity}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="quantity-slider"
              />
            </div>
          )}
          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">Confirm</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default GiveItemPlayerModal;