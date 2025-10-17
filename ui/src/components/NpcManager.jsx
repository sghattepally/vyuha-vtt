// ui/src/components/NpcManager.jsx (Redesigned)

import React, { useState, useEffect } from 'react';
import axios from 'axios';

function NpcManager({ gmId, sessionId, onClose }) {
  const [myNpcs, setMyNpcs] = useState([]);
  const [selectedNpcIds, setSelectedNpcIds] = useState(new Set());
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    axios.get(`http://localhost:8000/users/${gmId}/characters`)
      .then(res => setMyNpcs(res.data))
      .catch(err => console.error("Failed to fetch GM characters", err));
  }, [gmId]);

  const handleToggleNpc = (npcId) => {
    setSelectedNpcIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(npcId)) {
        newSet.delete(npcId);
      } else {
        newSet.add(npcId);
      }
      return newSet;
    });
  };

  const handleAddSelectedNpcs = async () => {
    if (selectedNpcIds.size === 0) return;
    setIsLoading(true);
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionId}/add_npcs`, {
        character_ids: Array.from(selectedNpcIds)
      });
      onClose(); // Close the modal on success
    } catch (err) {
      console.error("Failed to add NPCs", err);
      // Optionally show an error message to the user here
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h2>Manage NPCs</h2>
        <div className="npc-list">
          {myNpcs.length > 0 ? myNpcs.map(npc => (
            <div key={npc.id} className="npc-list-item">
              <label>
                <input
                  type="checkbox"
                  checked={selectedNpcIds.has(npc.id)}
                  onChange={() => handleToggleNpc(npc.id)}
                />
                {npc.name} - Lvl {npc.level} {npc.character_class}
              </label>
            </div>
          )) : <p>You have not created any NPC templates.</p>}
        </div>
        <div className="modal-actions">
          <button type="button" onClick={onClose}>Cancel</button>
          <button 
            type="button" 
            onClick={handleAddSelectedNpcs}
            disabled={isLoading || selectedNpcIds.size === 0}
          >
            {isLoading ? 'Adding...' : `Add ${selectedNpcIds.size} to Session`}
          </button>
        </div>
      </div>
    </div>
  );
}

export default NpcManager;