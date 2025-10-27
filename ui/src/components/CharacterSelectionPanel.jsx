// ui/src/components/CharacterSelectionPanel.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function CharacterSelectionPanel({ sessionData, playerData }) {
  const [campaignCharacters, setCampaignCharacters] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Debug logging
  console.log('CharacterSelectionPanel Debug:', {
    hasCampaignId: !!sessionData?.campaign_id,
    campaign_id: sessionData?.campaign_id,
    charactersLoaded: !!campaignCharacters,
    playerData: playerData
  });

  useEffect(() => {
    if (sessionData?.campaign_id) {
      // Fetch campaign characters
      axios.get(`http://localhost:8000/campaigns/${sessionData.campaign_id}/characters`)
        .then(response => setCampaignCharacters(response.data))
        .catch(error => console.error("Failed to fetch campaign characters", error));
    }
  }, [sessionData?.campaign_id]);

  const handleSelectCharacter = async (characterId) => {
    setIsLoading(true);
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/select_character`, {
        player_id: playerData.id,
        character_id: characterId
      });
    } catch (error) {
      console.error("Failed to select character", error);
      alert(error.response?.data?.detail || "Failed to select character");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeselectCharacter = async () => {
    setIsLoading(true);
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/deselect_character`, {
        player_id: playerData.id
      });
    } catch (error) {
      console.error("Failed to deselect character", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!sessionData?.campaign_id) {
    return (
      <div className="character-selection-panel">
        <p className="placeholder-text">Waiting for GM to select a campaign...</p>
      </div>
    );
  }

  if (!campaignCharacters) {
    return (
      <div className="character-selection-panel">
        <p className="placeholder-text">Loading characters...</p>
      </div>
    );
  }

  // Get current selections
  const selections = sessionData.character_selections || {};
  const mySelection = selections[playerData.id];
  
  // Helper to check if character is selected by someone
  const isCharacterSelected = (charId) => {
    return Object.values(selections).includes(charId);
  };

  // Helper to check if character is selected by me
  const isMySelection = (charId) => {
    return mySelection === charId;
  };

  return (
    <div className="character-selection-panel">
      <h3>Choose Your Character</h3>
      
      {mySelection && (
        <div className="my-selection-banner">
          <p>You've selected: <strong>{campaignCharacters.player_characters.find(c => c.id === mySelection)?.name}</strong></p>
        </div>
      )}

      <div className="character-grid">
        {campaignCharacters.player_characters.map(character => {
          const selected = isCharacterSelected(character.id);
          const mine = isMySelection(character.id);
          const disabled = selected && !mine;

          return (
            <div 
              key={character.id} 
              className={`character-card ${selected ? 'selected' : ''} ${mine ? 'my-selection' : ''} ${disabled ? 'disabled' : ''}`}
            >
              <div className="character-header">
                <h4>{character.name}</h4>
                {selected && !mine && <span className="taken-badge">TAKEN</span>}
                {mine && <span className="my-badge">YOUR PICK</span>}
              </div>
              
              <div className="character-info">
                <p className="character-race-class">{character.race?.name} {character.char_class?.name}</p>
                <p className="character-level">Level {character.level}</p>
              </div>

              {character.backstory && (
                <p className="character-backstory">{character.backstory}</p>
              )}

              <div className="character-stats">
                <div className="stat-row">
                  <span>💪 {character.bala}</span>
                  <span>🎯 {character.dakshata}</span>
                  <span>❤️ {character.dhriti}</span>
                </div>
                <div className="stat-row">
                  <span>🧠 {character.buddhi}</span>
                  <span>✨ {character.prajna}</span>
                  <span>💫 {character.samkalpa}</span>
                </div>
              </div>

              {!mine && !disabled && (
                <button 
                  onClick={() => handleSelectCharacter(character.id)}
                  disabled={isLoading}
                  className="select-character-button"
                >
                  Select
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Show NPCs and Enemies for context */}
      {(campaignCharacters.npcs.length > 0 || campaignCharacters.enemies.length > 0) && (
        <div className="campaign-npcs-info">
          <h4>Campaign NPCs & Enemies</h4>
          <p className="info-text">These will be controlled by the GM during the campaign</p>
          
          {campaignCharacters.enemies.length > 0 && (
            <div className="enemy-list">
              <h5>Enemies:</h5>
              <ul>
                {campaignCharacters.enemies.map(enemy => (
                  <li key={enemy.id}>{enemy.name}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CharacterSelectionPanel;