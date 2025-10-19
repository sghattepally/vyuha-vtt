import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import GridLayout from 'react-grid-layout';
import Panel from './Panel';
import CombatGrid from './CombatGrid';
import InitiativeTracker from './InitiativeTracker';
import ActionPanel from './ActionPanel';
import GameLog from './GameLog';
import CharacterCard from './CharacterCard';
import Token from './Token';
import NpcManager from './NpcManager';
import PartyPanel from './PartyPanel';

const initialLayout = [
  { i: 'party', x: 0, y: 0, w: 6, h: 4, minW: 3, minH: 3 },
  { i: 'log', x: 6, y: 0, w: 5, h: 4, minW: 2, minH: 3 },
  { i: 'main', x: 3, y: 4, w: 8, h: 7, minW: 4, minH: 5 },
  { i: 'context', x: 0, y: 4, w: 3, h: 7, minW: 2, minH: 5 },
];
const COLLAPSED_HEIGHT = 1;

function GameRoom({ sessionData, currentUser, isGM, isGmOverride, dragPreviewRef , newLogTrigger }) {
  const [selectedAction, setSelectedAction] = useState({ type: 'none', ability: null });
  const [activeCharacterAbilities, setActiveCharacterAbilities] = useState([]);
  const [turnActions, setTurnActions] = useState({ hasAttacked: false });
  const [isNpcManagerOpen, setIsNpcManagerOpen] = useState(false);
  const [layout, setLayout] = useState(initialLayout);
  const originalLayouts = useRef({});
  const effectiveIsGM = isGM && isGmOverride;
  const handleLayoutChange = (newLayout) => {
    setLayout(newLayout);
  };


  const togglePanelCollapse = (panelKey) => {
    setLayout(prevLayout =>
      prevLayout.map(panel => {
        if (panel.i === panelKey) {
          const isCollapsed = panel.h === COLLAPSED_HEIGHT;

          if (isCollapsed) {
            // If it IS collapsed, restore it using the saved layout.
            const original = originalLayouts.current[panelKey];
            return {
              ...panel,
              h: original ? original.h : 3, // Restore height
              minH: original ? original.minH : 3, // Restore minHeight
              maxH: undefined, // Allow resizing again
            };
          } else {
            // *** THIS IS THE FIX ***
            // If it is NOT collapsed, save its current state BEFORE collapsing.
            originalLayouts.current[panelKey] = { ...panel };

            return {
              ...panel,
              h: COLLAPSED_HEIGHT,
              minH: COLLAPSED_HEIGHT,
              maxH: COLLAPSED_HEIGHT, // Prevent resizing while collapsed
            };
          }
        }
        return panel;
      })
    );
  };

  const handlePrepareForCombat = async () => {
    if (!effectiveIsGM) return;
    try {

      await axios.patch(`http://localhost:8000/sessions/${sessionData.id}/`, {
        current_mode: 'staging'
      });
    } catch (err) {
      console.error("Failed to prepare for combat", err);
    }
  };

  const handleTokenMove = async (participantId, x, y) => {
    if (!effectiveIsGM) return;
    try {
      await axios.patch(`http://localhost:8000/sessions/${sessionData.id}/`, {
        participant_positions: [{ participant_id: participantId, x_pos: x, y_pos: y }]
      });
    } catch (err) {
      console.error("Failed to move token", err);
    }
  };
  const handleBeginCombat = async () => {
    if (!effectiveIsGM) return;
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/begin_combat`);
    } catch (err) {
      console.error("Failed to begin combat", err);
    }
  };
  const handlePerformAction = async (actionPayload) => {
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/action`, actionPayload);
      if (actionPayload.action_type === 'ATTACK') setTurnActions({ hasAttacked: true });
      setSelectedAction({ type: 'none', ability: null });
    } catch (err) { console.error("Action failed:", err.response?.data?.detail || err); }
  };

  const handleEndTurn = async () => {
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/next_turn`);
      setTurnActions({ hasAttacked: false });
      setSelectedAction({ type: 'none', ability: null });
    } catch (err) { console.error("Failed to end turn:", err); }
  };
  const handleEndCombat = async () => {
    if (!effectiveIsGM) return;
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/end_combat`);
    } catch (err) { console.error("Failed to end combat:", err); }
  };

  const activeParticipant = sessionData?.turn_order?.length > 0
    ? sessionData.participants.find(p => p.id === sessionData.turn_order[sessionData.current_turn_index])
    : null;
  const isMyTurn = activeParticipant && (activeParticipant.player_id === currentUser.id || effectiveIsGM);

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
    <>
      {isNpcManagerOpen && (
        <NpcManager
          gmId={currentUser.id}
          sessionId={sessionData.id}
          sessionParticipants={sessionData.participants}
          onClose={() => setIsNpcManagerOpen(false)}
        />
      )}
      <div className="game-room-dynamic">
        <GridLayout
          className="layout"
          layout={layout}
          cols={12}
          rowHeight={60}
          width={window.innerWidth} // Make it responsive to window size
          onLayoutChange={handleLayoutChange}
          draggableHandle=".panel-header"
          draggableCancel=".panel-collapse-button"
        >
          <div key="party" className="allow-overflow">
            <Panel title="Party" onCollapse={() => togglePanelCollapse('party')}
              isCollapsed={layout.find(p => p.i === 'party')?.h === COLLAPSED_HEIGHT}>
              <PartyPanel
              participants={sessionData.participants}
              currentUser={currentUser}
              isGM={effectiveIsGM}
              dragPreviewRef={dragPreviewRef}
              sessionMode={sessionData.current_mode}
            />
            </Panel>
          </div>

          <div key="log">
            <Panel title="Game Log" onCollapse={() => togglePanelCollapse('log')}
              isCollapsed={layout.find(p => p.i === 'log')?.h === COLLAPSED_HEIGHT}>
              <GameLog 
            sessionId={sessionData.id} 
      participants={sessionData.participants}
      newLogTrigger={newLogTrigger} />
            </Panel>
          </div>

          <div key="main">
            <Panel title="The World" onCollapse={() => togglePanelCollapse('main')}
              isCollapsed={layout.find(p => p.i === 'main')?.h === COLLAPSED_HEIGHT}>


              {sessionData.current_mode === 'exploration' && (
                <div className="exploration-view">
                </div>
              )}
              {(sessionData.current_mode === 'staging' || sessionData.current_mode === 'combat') && (
                <div className="staging-layout">
                  <div className="grid-container">
                    <CombatGrid
                      participants={onGridParticipants}
                      isGM={isGM}
                      // --- RECONNECT EXISTING HANDLERS ---
                      onTokenMove={handleTokenMove}
                      onGridClick={handleGridClick}
                      onTokenClick={handleTokenClick}

                      activeParticipantId={activeParticipant?.id}
                      showMovementFor={selectedAction.type === 'MOVE' && isMyTurn ? activeParticipant : null}

                      // --- ADD DROP FUNCTIONALITY ---
                      onDragOver={(e) => e.preventDefault()} // This is required to allow a drop
                      onDrop={(e) => {
                        e.preventDefault();
                        const participantId = e.dataTransfer.getData("participantId");

                        // Calculate grid coordinates from the drop position
                        const gridRect = e.currentTarget.getBoundingClientRect();
                        const x = Math.floor((e.clientX - gridRect.left) / 50); // Assumes 50px grid cells
                        const y = Math.floor((e.clientY - gridRect.top) / 50);

                        // Call the existing function to update the backend
                        if (participantId) {
                          handleTokenMove(participantId, x, y);
                        }
                      }}
                    />
                  </div>
                </div>
              )}

            </Panel>
          </div>

          <div key="context">
            <Panel title="Context" onCollapse={() => togglePanelCollapse('context')}
            contentClassName="context-panel-content"
              isCollapsed={layout.find(p => p.i === 'context')?.h === COLLAPSED_HEIGHT}>
              {effectiveIsGM && (
                <div className="gm-context-controls">
                  {/* These buttons only show during EXPLORATION */}
                  {sessionData.current_mode === 'exploration' && (
                    <>
                      <button onClick={handlePrepareForCombat}>Prepare for Combat</button>
                      <button onClick={() => setIsNpcManagerOpen(true)}>Manage NPCs</button>
                    </>
                  )}
                  {sessionData.current_mode === 'staging' && (
                    <button onClick={handleBeginCombat}>Begin Combat</button>
                  )}
                  {sessionData.current_mode === 'combat' && (
      <button className = "gm-end-combat-btn" onClick={handleEndCombat}>
        End Combat
      </button>
    )}
                </div>
              )}
              {sessionData.current_mode === 'combat' ? (
                <>
                  <InitiativeTracker participants={sessionData.participants} turnOrder={sessionData.turn_order} currentTurnIndex={sessionData.current_turn_index} />
                  <ActionPanel 
                  abilities={activeCharacterAbilities} 
                  isMyTurn={isMyTurn} 
                  activeParticipant={activeParticipant} 
                  selectedAction={selectedAction} 
                  turnActions={turnActions} 
                  onSelectMove={() => setSelectedAction({ type: 'MOVE' })}
                  onSelectAbility={(ability) => setSelectedAction({ type: 'TARGETING', ability })} 
                    onEndTurn={handleEndTurn} />
                </>
              ) : (
                <div className="placeholder-text">Character details will appear here.</div>
              )}
            </Panel>
          </div>
        </GridLayout>
      </div>
    </>);
}

export default GameRoom;