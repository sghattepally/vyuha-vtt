// ui/src/components/LobbyWithCampaign.jsx

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import CampaignSelector from './CampaignSelector';
import CharacterSelectionPanel from './CharacterSelectionPanel';
import CharacterCreator from './CharacterCreator';
import NpcManager from './NpcManager';
import GameLog from './GameLog';

function Lobby({ sessionData, playerData, newLogTrigger }) {
  const [playersInLobby, setPlayersInLobby] = useState([]);
  const [myCharacters, setMyCharacters] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isNpcManagerOpen, setIsNpcManagerOpen] = useState(false);
  const [campaignCharacters, setCampaignCharacters] = useState(null);


  const isGM = !!(playerData && sessionData && playerData.id === sessionData.gm_id);
  const hasCampaign = !!sessionData?.campaign_id;

  const playerCharacterMap = React.useMemo(() => {
    const map = new Map();
    sessionData?.participants.forEach(participant => {
      if (participant.player_id) {
        map.set(participant.player_id, participant.character.name);
      }
    });
    return map;
  }, [sessionData]);

  const myParticipantEntry = sessionData?.participants.find(p => p.player_id === playerData?.id);

  // Fetch player's characters (for non-campaign mode)
  const fetchMyCharacters = useCallback(() => {
    if (playerData?.id && !isGM && !hasCampaign) {
      axios.get(`http://localhost:8000/users/${playerData.id}/characters`)
        .then(response => setMyCharacters(response.data))
        .catch(error => console.error("Failed to fetch characters", error));
    }
  }, [playerData?.id, isGM, hasCampaign]);

  useEffect(() => {
    if (sessionData?.id) {
      axios.get(`http://localhost:8000/sessions/${sessionData.id}/players`)
        .then(response => setPlayersInLobby(response.data));
    }
    fetchMyCharacters();
  }, [sessionData, fetchMyCharacters]);

  useEffect(() => {
  if (hasCampaign && sessionData?.campaign_id) {
    axios.get(`http://localhost:8000/campaigns/${sessionData.campaign_id}/characters`)
      .then(response => setCampaignCharacters(response.data))
      .catch(error => console.error("Failed to fetch campaign characters", error));
  }
}, [hasCampaign, sessionData?.campaign_id]);

  const handleStartGame = async () => {
    if (!isGM) return;
    
    // If campaign mode, use campaign start
    if (hasCampaign) {
      try {
        await axios.post(`http://localhost:8000/sessions/${sessionData.id}/start_with_campaign`);
      } catch (error) {
        console.error("Failed to start campaign", error);
        alert(error.response?.data?.detail || "Failed to start campaign");
      }
    } else {
      // Regular mode
      try {
        await axios.patch(`http://localhost:8000/sessions/${sessionData.id}/`, {
          current_mode: 'exploration'
        });
      } catch (error) {
        console.error("Failed to start game", error);
      }
    }
  };

  const handleSelectCharacter = async (characterId) => {
    setIsLoading(true);
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/add_character`, {
        player_id: playerData.id,
        character_id: characterId
      });
    } catch (error) {
      console.error("Failed to select character", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveCharacter = async (participantId) => {
    try {
      await axios.delete(`http://localhost:8000/sessions/${sessionData.id}/participants/${participantId}`);
    } catch (error) {
      console.error("Failed to remove character", error);
    }
  };

  // Count selected characters in campaign mode
  const selectedCount = hasCampaign ? Object.keys(sessionData.character_selections || {}).length : 0;
const canStart = isGM && (hasCampaign ? selectedCount > 0 : sessionData.participants.length > 0);

  return (
    <div className="lobby-page lobby-with-campaign">
    <div className="lobby-left-content">
        <h1>{sessionData.campaign_name || "Game Lobby"}</h1>
        
        {/* Access Code */}
        <div className="access-code">
          <p>Share this code with your players:</p>
          <strong>{sessionData.access_code}</strong>
        </div>

        {/* GM Campaign Selection */}
        {isGM && !hasCampaign && (
          <CampaignSelector 
            sessionId={sessionData.id}
            sessionData={sessionData}
          />
        )}

        {/* Traditional Character Selection (Non-Campaign Mode) */}
        {!hasCampaign && !isGM && (
          <div className="traditional-character-selection">
            <h3>Your Characters</h3>
            
            {myParticipantEntry ? (
              <div className="selected-character">
                <p>You are playing as: <strong>{myParticipantEntry.character.name}</strong></p>
                <button 
                  onClick={() => handleRemoveCharacter(myParticipantEntry.id)}
                  className="remove-character-button"
                >
                  Change Character
                </button>
              </div>
            ) : (
              <>
                {myCharacters.length === 0 ? (
                  <p>You have no characters. Create one below!</p>
                ) : (
                  <div className="character-list">
                    {myCharacters.map(char => (
                      <div key={char.id} className="character-option">
                        <span>{char.name} ({char.race?.name} {char.char_class?.name})</span>
                        <button 
                          onClick={() => handleSelectCharacter(char.id)}
                          disabled={isLoading}
                        >
                          Select
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                
                <button 
                  onClick={() => setIsCreating(true)}
                  className="create-character-button"
                >
                  Create New Character
                </button>
              </>
            )}
          </div>
        )}
          {/* Campaign Info Display (for all users when campaign selected) */}
        {hasCampaign && (
          <CampaignSelector 
            sessionId={sessionData.id}
            sessionData={sessionData}
          />
        )}

        {/* Players in Lobby */}
        <div className="player-list">
          <h3>Players in Lobby ({playersInLobby.length})</h3>
          <ul>
            {playersInLobby.map(player => {
              let characterName = null;
              
              // Campaign mode - get character from selections
              if (hasCampaign && sessionData.character_selections) {
                const selectedCharId = sessionData.character_selections[player.id];
                if (selectedCharId && campaignCharacters?.player_characters) {
                  const char = campaignCharacters.player_characters.find(c => c.id === selectedCharId);
                  characterName = char?.name;
                }
              } else {
                // Non-campaign mode - use participant map
                characterName = playerCharacterMap.get(player.id);
              }
              
              return (
                <li key={player.id}>
                  {player.display_name}
                  {characterName && (
                    <span className="player-character"> ({characterName})</span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>

        {/* Campaign Selection Status */}
        {hasCampaign && (
          <div className="campaign-status">
            <h4>Campaign Status</h4>
            <p>{selectedCount} of {playersInLobby.length - 1} players ready</p>
            {isGM && selectedCount === 0 && (
              <p className="warning-text">Waiting for players to select characters...</p>
            )}
          </div>
        )}
        {/* Campaign NPCs & Enemies Info */}
        {hasCampaign && (
          <div className="campaign-npcs-info">
            <h4>Campaign NPCs & Enemies</h4>
            <p className="info-text">These will be controlled by the GM during the campaign</p>
            {/* This will be populated by fetching campaign data */}
          </div>
        )}

        {/* GM Controls */}
        {isGM && (
          <div className="gm-lobby-controls">
            {!hasCampaign && (
              <button 
                onClick={() => setIsNpcManagerOpen(true)}
                className="manage-npc-button"
              >
                Manage NPCs
              </button>
            )}
            
            <button 
              onClick={handleStartGame}
              disabled={!canStart}
              className="start-game-button"
            >
              {hasCampaign ? 'Start Campaign' : 'Start Game'}
            </button>
            
            {!canStart && hasCampaign && (
              <p className="info-text">At least one player must select a character</p>
            )}
          </div>
        )}
      </div>
        <div className="lobby-right-sidebar">
          {/* Character Selection Panel (moved here) */}
          {hasCampaign && !isGM && (
            <div className="lobby-character-panel">
              <CharacterSelectionPanel 
                sessionData={sessionData}
                playerData={playerData}
              />
            </div>
          )}
      {/* Game Log */}
      <div className="lobby-game-log">
        <GameLog sessionId={sessionData.id} newLogTrigger={newLogTrigger} />
      </div>

      {/* Modals */}
      {isCreating && (
        <CharacterCreator 
          playerId={playerData.id}
          onClose={() => setIsCreating(false)}
          onCharacterCreated={() => {
            setIsCreating(false);
            fetchMyCharacters();
          }}
        />
      )}

      {isNpcManagerOpen && (
        <NpcManager 
          sessionId={sessionData.id}
          gmId={playerData.id}
          onClose={() => setIsNpcManagerOpen(false)}
        />
      )}
    </div>
    </div>
  );
}

export default Lobby;