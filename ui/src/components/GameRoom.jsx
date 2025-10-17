// ui/src/components/GameRoom.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import CombatGrid from './CombatGrid';
import InitiativeTracker from './InitiativeTracker';
import ActionPanel from './ActionPanel';
import GameLog from './GameLog';
import CharacterCard from './CharacterCard';
import Token from './Token';

function GameRoom({ sessionData, currentUser, isGM }) {
  const [selectedAction, setSelectedAction] = useState({ type: 'none', ability: null });
const [activeCharacterAbilities, setActiveCharacterAbilities] = useState([]);
  const [turnActions, setTurnActions] = useState({ hasAttacked: false });
  const handlePrepareForCombat = async () => {
    if (!isGM) return;
    try {
      
      await axios.patch(`http://localhost:8000/sessions/${sessionData.id}/`, {
        current_mode: 'staging'
      });
    } catch (err) {
      console.error("Failed to prepare for combat", err);
    }
  };

  const handleTokenMove = async (participantId, x, y) => {
    if (!isGM) return;
    try {
      await axios.patch(`http://localhost:8000/sessions/${sessionData.id}/`, {
        participant_positions: [{ participant_id: participantId, x_pos: x, y_pos: y }]
      });
    } catch (err) {
      console.error("Failed to move token", err);
    }
  };
const handleBeginCombat = async () => {
    if (!isGM) return;
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/begin_combat`);
    } catch (err) {
      console.error("Failed to begin combat", err);
    }
  };
  const handlePerformAction = async (actionPayload) => {
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/action`, actionPayload);
      if (actionPayload.action_type === 'ATTACK') {
        setTurnActions({ hasAttacked: true });
      }
      setSelectedAction({ type: 'none', ability: null });
    } catch (err) {
      console.error("Action failed:", err.response?.data?.detail || err);
    }
  };
  const handleEndTurn = async () => {
    try {
        await axios.post(`http://localhost:8000/sessions/${sessionData.id}/next_turn`);
        setTurnActions({ hasAttacked: false });
        setSelectedAction({ type: 'none', ability: null });
    } catch (err) {
        console.error("Failed to end turn:", err);
    }
  };

  const handleEndCombat = async () => {
    if (!isGM) return;
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/end_combat`);
    } catch (err) { console.error("Failed to end combat:", err); }
  };

const activeParticipant = sessionData?.turn_order?.length > 0
    ? sessionData.participants.find(p => p.id === sessionData.turn_order[sessionData.current_turn_index])
    : null;
  const isMyTurn = activeParticipant && (activeParticipant.player_id === currentUser.id || isGM);

  const handleGridClick = (x, y) => {
    if (selectedAction.type === 'MOVE' && activeParticipant && isMyTurn) {
      handlePerformAction({ actor_id: activeParticipant.id, action_type: 'MOVE', new_x: x, new_y: y });
    }
  };
  const handleTokenClick = (targetId) => {
    if (selectedAction.type === 'TARGETING' && activeParticipant && isMyTurn) {
      handlePerformAction({ actor_id: activeParticipant.id, action_type: 'ATTACK', target_id: targetId, ability_id: selectedAction.ability.id });
    }
  };

  useEffect(() => {
    setActiveCharacterAbilities([]);
    if (activeParticipant) {
      axios.get(`http://localhost:8000/characters/${activeParticipant.character.id}/abilities/`)
        .then(res => {
          setActiveCharacterAbilities(res.data);
        })
        .catch(err => {
          console.error("Failed to fetch abilities", err);
          setActiveCharacterAbilities([]);
        });
    }
  }, [activeParticipant]);

  if (!sessionData) return <div>Loading Game Session...</div>;

  const onGridParticipants = sessionData.participants.filter(p => p.x_pos !== null && p.x_pos !== undefined);
  const offGridParticipants = sessionData.participants.filter(p => p.x_pos === null || p.x_pos === undefined);

  return (
    <div className="game-room">
      <h1>{sessionData.campaign_name}</h1>
      <p>Current Mode: <strong>{sessionData.current_mode.toUpperCase()}</strong></p>

      {/* Exploration Mode */}
      {sessionData.current_mode === 'exploration' && (
        <div className="exploration-view">
          {isGM && (
            <div className="gm-controls">
              <button onClick={handlePrepareForCombat}>Prepare for Combat</button>
            </div>
          )}
          <h3>Party Members</h3>
          <div className="participants-grid">
            {sessionData.participants.map((p) => (
              <CharacterCard key={p.id} participant={p} />
            ))}
          </div>
        </div>
      )}

      {/* Staging Mode */}
      {sessionData.current_mode === 'staging' && (
         <div className="staging-view">
            <h3>Staging Phase: Place Tokens!</h3>
            <div className="gm-controls">
                <button onClick={handleBeginCombat}>Begin Combat!</button>
            </div>
            <div className="staging-layout">
              <CombatGrid
                  participants={onGridParticipants}
                  isGM={isGM}
                  onTokenMove={handleTokenMove}
              />
              {isGM && offGridParticipants.length > 0 && (
                <div className="token-shelf">
                  <h4>Available Tokens</h4>
                  {offGridParticipants.map(p => (
                    <div
                      key={p.id}
                      className="token-on-shelf"
                      draggable
                      onDragStart={(e) => e.dataTransfer.setData("participantId", p.id)}
                    >
                      <Token participant={p} />
                    </div>
                  ))}
                </div>
              )}
            </div>
        </div>
      )}
      
      {/* Combat Mode */}
      {sessionData.current_mode === 'combat' && (
        <div className="combat-view">
          <div className="combat-main-panel">
            
            <CombatGrid 
              participants={onGridParticipants}
              isGM={isGM}
              activeParticipantId={activeParticipant?.id}
              onGridClick={handleGridClick}
              onTokenClick={handleTokenClick}
              showMovementFor={selectedAction.type === 'MOVE' && isMyTurn ? activeParticipant : null}
            />
          </div>
          <div className="combat-side-panel">
            <InitiativeTracker participants={sessionData.participants} turnOrder={sessionData.turn_order} currentTurnIndex={sessionData.current_turn_index} />
            <ActionPanel abilities={activeCharacterAbilities} isMyTurn={isMyTurn} activeParticipant={activeParticipant} selectedAction={selectedAction} turnActions={turnActions} onSelectMove={() => setSelectedAction({ type: 'MOVE' })} onSelectAbility={(ability) => setSelectedAction({ type: 'TARGETING', ability })} onEndTurn={handleEndTurn}/>
            <GameLog messages={sessionData.log || []} />
            {isGM && <button className="gm-end-combat-btn" onClick={handleEndCombat}>End Combat</button>}
          </div>
        </div>
      )}
    </div>
  );
}

export default GameRoom;