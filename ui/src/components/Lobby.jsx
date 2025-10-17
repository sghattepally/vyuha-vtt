// ui/src/components/Lobby.jsx (Final Version)

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import CharacterCreator from './CharacterCreator'; // Import the new component
import NpcManager from './NpcManager';

function Lobby({ sessionData, playerData }) {
  const [playersInLobby, setPlayersInLobby] = useState([]);
  const [myCharacters, setMyCharacters] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false); // State to control the modal
  const [isNpcManagerOpen, setIsNpcManagerOpen] = useState(false);

  const isGM = !!(playerData && sessionData && playerData.id === sessionData.gm_id);

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

  // Reusable function to fetch the player's characters
  const fetchMyCharacters = useCallback(() => {
    if (playerData?.id && !isGM) {
      axios.get(`http://localhost:8000/users/${playerData.id}/characters`)
        .then(response => setMyCharacters(response.data))
        .catch(error => console.error("Failed to fetch characters", error));
    }
  }, [playerData?.id, isGM]);

  useEffect(() => {
    if (sessionData?.id) {
      axios.get(`http://localhost:8000/sessions/${sessionData.id}/players`)
        .then(response => setPlayersInLobby(response.data));
    }
    fetchMyCharacters();
  }, [sessionData, fetchMyCharacters]);

  const handleStartGame = async () => {
    if (!isGM) return;
    try {
      await axios.patch(`http://localhost:8000/sessions/${sessionData.id}/`, {
        current_mode: 'exploration'
      });
    } catch (error) {
      console.error("Failed to start game", error);
    }
  };

  const handleSelectCharacter = async (characterId) => {
    setIsLoading(true);
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/add_character`, {
        player_id: playerData.id,
        character_id: characterId
      });
      // The WebSocket will broadcast the update, so no need to set state here.
    } catch (error) {
      console.error("Failed to select character", error.response?.data?.detail || error);
    } finally {
      setIsLoading(false);
    }
  };
const handleCharacterCreated = () => {
    setIsCreating(false); // Close the modal
    fetchMyCharacters(); // Refresh the character list
  };

const handleDeselectCharacter = async () => {
    if (!myParticipantEntry) return; // Safety check
    setIsLoading(true);
    try {
      await axios.delete(`http://localhost:8000/sessions/${sessionData.id}/participants/${myParticipantEntry.id}`);
      // The WebSocket will handle the UI update automatically.
    } catch (error) {
      console.error("Failed to deselect character", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!sessionData || !playerData) return <div>Loading lobby...</div>;

  return (
    <>
      {isCreating && (
        <CharacterCreator
          ownerId={playerData.id}
          onCharacterCreated={handleCharacterCreated}
          onClose={() => setIsCreating(false)}
        />
      )}
      {isNpcManagerOpen && (
        <NpcManager
          gmId={playerData.id}
          sessionId={sessionData.id}
          onClose={() => setIsNpcManagerOpen(false)}
        />
      )}
    <div className="lobby-page">
      <h1>Campaign: {sessionData.campaign_name}</h1>
      <h2>Lobby</h2>
      
      {isGM && (
        <div className="access-code">
          Share this code with your players:
          <strong>{sessionData.access_code}</strong>
        </div>
      )}

      <div className="player-list">
        <h3>Players in Lobby: ({playersInLobby.length})</h3>
        <ul>
          {playersInLobby.map(player => {
            const characterName = playerCharacterMap.get(player.id);
            return (
                <li key={player.id}>
                  {player.display_name} {player.id === sessionData.gm_id ? '(GM)' : ''}
                  {characterName && <span className="selected-character-tag">({characterName})</span>}
                </li>
            );
          })}
        </ul>
      </div>

      {!isGM && (
          <div className="character-selection">
            {myParticipantEntry ? (
              // If a character IS selected, show this UI:
              <div className="character-selected-view">
                <h4>Character Selected</h4>
                <p>{myParticipantEntry.character.name}</p>
                <button onClick={handleDeselectCharacter} disabled={isLoading}>
                  Change Character
                </button>
              </div>
            ) : (
              // If NO character is selected, show this UI:
              <>
                <h4>Choose Your Character</h4>
                {myCharacters.length > 0 ? (
                  <ul className="character-list">
                    {myCharacters.map(char => (
                      <li key={char.id}>
                        <span>{char.name} - Lvl {char.level} {char.character_class}</span>
                        <button 
                          onClick={() => handleSelectCharacter(char.id)} 
                          disabled={isLoading}
                        >
                          Select
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>You have no characters. Create one to begin!</p>
                )}
                <button onClick={() => setIsCreating(true)} className="create-char-button">
                  Create New Character
                </button>
              </>
            )}
          </div>
        )}

      {isGM && (
        <div className="gm-lobby-controls">
        <button onClick={() => setIsCreating(true)} className="manage-npc-button">
            Create NPC Template
          </button>
        <button onClick={() => setIsNpcManagerOpen(true)} className="manage-npc-button">
              Manage NPCs
            </button>
        <button onClick={handleStartGame} className="start-game-button">
          Start Game
        </button>
      </div>
      )}
      {!isGM && !myParticipantEntry && <p>Select a character to be ready.</p>}
      {!isGM && myParticipantEntry && <p className="waiting-text">Waiting for the GM to start the game...</p>}
    </div>
    </>
  );
}

export default Lobby;