import React, { useState, useEffect } from 'react';
import axios from 'axios';

// The component is now robust enough to handle a missing sessionParticipants prop.
function NpcManager({ sessionId, sessionParticipants, gmId, onClose }) {
  const [allGmCharacters, setAllGmCharacters] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const [selectedNpcIds, setSelectedNpcIds] = useState(() => {
    // --- THIS IS THE FIX ---
    // We now check if sessionParticipants is a valid array before trying to use it.
    // If it's not, we default to an empty array, preventing the crash.
    const initialParticipants = Array.isArray(sessionParticipants) ? sessionParticipants : [];
    
    const initialIds = initialParticipants
      .filter(p => p.player_id === null || p.player_id === gmId) // Caters to our new backend logic
      .map(p => p.character.id);
    return new Set(initialIds);
  });

  useEffect(() => {
    if (!gmId) {
      setError("GM ID is missing. Cannot load characters.");
      setIsLoading(false);
      return;
    }
    axios.get(`http://localhost:8000/users/${gmId}/characters/`)
      .then(res => {
        setAllGmCharacters(res.data);
        setIsLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch GM characters:", err);
        setError("Could not load character templates.");
        setIsLoading(false);
      });
  }, [gmId]);

  const handleCheckboxChange = (characterId) => {
    setSelectedNpcIds(prevIds => {
      const newIds = new Set(prevIds);
      if (newIds.has(characterId)) {
        newIds.delete(characterId);
      } else {
        newIds.add(characterId);
      }
      return newIds;
    });
  };

  const handleUpdateSession = () => {
    const npcIdList = Array.from(selectedNpcIds);
    axios.post(`http://localhost:8000/sessions/${sessionId}/update_npcs/`, {
      npc_ids: npcIdList
    })
    .then(() => {
      onClose();
    })
    .catch(err => {
      console.error("Failed to update session NPCs:", err);
      setError("An error occurred while updating the session.");
    });
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <h2>Manage NPCs in Session</h2>
        <div className="npc-list">
          {isLoading ? (
            <p>Loading characters...</p>
          ) : error ? (
            <p className="error-message">{error}</p>
          ) : allGmCharacters.length > 0 ? (
            allGmCharacters.map(char => (
              <div key={char.id} className="npc-list-item">
                <label>
                  <input
                    type="checkbox"
                    checked={selectedNpcIds.has(char.id)}
                    onChange={() => handleCheckboxChange(char.id)}
                  />
                  {char.name} - ({char.character_class})
                </label>
              </div>
            ))
          ) : (
            <p>No character templates found. Create some first!</p>
          )}
        </div>
        <div className="modal-actions">
          <button onClick={handleUpdateSession} disabled={isLoading}>Update Session</button>
          <button onClick={onClose} className="button-secondary">Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default NpcManager;