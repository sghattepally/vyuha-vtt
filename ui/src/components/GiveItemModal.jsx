import React, { useState, useEffect } from 'react';
import axios from 'axios';

function GiveItemModal({ participants, onClose, onGiveItem }) {
  const [itemList, setItemList] = useState([]);
  const [selectedCharId, setSelectedCharId] = useState('');
  const [selectedItemId, setSelectedItemId] = useState('');
  const [quantity, setQuantity] = useState(1);

  // Fetch the master item list when the modal opens
  useEffect(() => {
    axios.get('http://localhost:8000/items')
      .then(response => {
        setItemList(response.data);
        // Pre-select the first item if the list is not empty
        if (response.data.length > 0) {
          setSelectedItemId(response.data[0].id);
        }
      })
      .catch(error => console.error("Failed to fetch item list:", error));
  }, []);

  // Pre-select the first participant
  useEffect(() => {
    if (participants.length > 0) {
      setSelectedCharId(participants[0].character.id);
    }
  }, [participants]);


  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedCharId || !selectedItemId || quantity < 1) {
      alert("Please select a character, an item, and a valid quantity.");
      return;
    }
    onGiveItem({
      character_id: parseInt(selectedCharId),
      item_id: parseInt(selectedItemId),
      quantity: parseInt(quantity),
    });
  };

  const playerParticipants = participants.filter(p => p.character && p.player_id);

  return (
    <div className="modal-backdrop">
      <div className="modal give-item-modal">
        <h2>Give Item</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Character</label>
            <select value={selectedCharId} onChange={(e) => setSelectedCharId(e.target.value)}>
              {playerParticipants.map(p => (
                <option key={p.character.id} value={p.character.id}>
                  {p.character.name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Item</label>
            <select value={selectedItemId} onChange={(e) => setSelectedItemId(e.target.value)}>
              {itemList.map(item => (
                <option key={item.id} value={item.id}>
                  {item.puranic_name} ({item.item_type})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Quantity</label>
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              min="1"
              required
            />
          </div>
          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">Give Item</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default GiveItemModal;