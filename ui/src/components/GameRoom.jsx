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

function GameRoom({ sessionData, currentUser, isGM }) {
  const [selectedAction, setSelectedAction] = useState({ type: 'none', ability: null });
  const [activeCharacterAbilities, setActiveCharacterAbilities] = useState([]);
  const [turnActions, setTurnActions] = useState({ hasAttacked: false });
  const [isNpcManagerOpen, setIsNpcManagerOpen] = useState(false);

  // --- Layout State Management ---
  const [layout, setLayout] = useState([
    { i: 'party', x: 0, y: 0, w: 12, h: 3, minW: 3, minH: 3 },
    { i: 'log', x: 9, y: 3, w: 3, h: 9, minW: 2, minH: 4 },
    { i: 'main', x: 3, y: 3, w: 6, h: 9, minW: 4, minH: 5 },
    { i: 'context', x: 0, y: 3, w: 3, h: 9, minW: 2, minH: 5 },
  ]);
  const originalLayouts = useRef({});

  const handleLayoutChange = (newLayout) => {
    // This logic prevents resizing/dragging from breaking the collapse state
    const updatedLayout = newLayout.map(newItem => {
        const existingItem = layout.find(item => item.i === newItem.i);
        if (existingItem && existingItem.h === 1) {
            return { ...newItem, h: 1, minH: 1 }; // Keep it collapsed
        }
        return newItem;
    });
    setLayout(updatedLayout);
  };
const COLLAPSED_HEIGHT = 1;

const togglePanelCollapse = (panelKey) => {
  setLayout(prevLayout => {
    // Create a new array to ensure React triggers a re-render
    const newLayout = prevLayout.map(panel => {
      if (panel.i === panelKey) {
        // Create a new panel object for immutability
        const newPanel = { ...panel };

        if (panel.h !== COLLAPSED_HEIGHT) {
          // If not collapsed, store original height and collapse it
          newPanel.original_h = panel.h; // Store the height
          newPanel.h = COLLAPSED_HEIGHT;
        } else {
          // If collapsed, restore it to its original height or a default
          newPanel.h = newPanel.original_h || 3; // Restore or use a default
        }
        return newPanel;
      }
      return panel;
    });
    return newLayout;
  });
};

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
const effectiveIsGM = isGM || isGmOverride;
  if (!sessionData) return <div>Loading Game Session...</div>;

  const onGridParticipants = sessionData.participants.filter(p => p.x_pos !== null && p.x_pos !== undefined);
  const offGridParticipants = sessionData.participants.filter(p => p.x_pos === null || p.x_pos === undefined);

  return (
    <>
    {isNpcManagerOpen && (
        <NpcManager
          gmId={currentUser.id}
          sessionId={sessionData.id}
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
      >
        <div key="party">
          <Panel title="Party" onToggleCollapse={() => togglePanelCollapse('party')}>
            <div className="participants-grid-horizontal">
              {sessionData.participants.map((p) => (<CharacterCard key={p.id} participant={p} />))}
            </div>
          </Panel>
        </div>
        
        <div key="log">
          <Panel title="Game Log" onToggleCollapse={() => togglePanelCollapse('log')}>
            <GameLog messages={sessionData.log || []} />
          </Panel>
        </div>

        <div key="main">
          <Panel title="The World" onToggleCollapse={() => togglePanelCollapse('main')}>
            
            
            {sessionData.current_mode === 'exploration' && (
                <div className="exploration-view">
                  {effectiveIsGM && (
                    <div className="gm-controls">
                      <button onClick={handlePrepareForCombat}>Prepare for Combat</button>
                      <button onClick={() => setIsNpcManagerOpen(true)}>Manage NPCs</button>
                    </div>
                  )}
                  <div className="participants-grid">
                    {sessionData.participants.map((p) => (<CharacterCard key={p.id} participant={p} />))}
                  </div>
                </div>
              )}
            {(sessionData.current_mode === 'staging' || sessionData.current_mode === 'combat') && (
              <div className="staging-layout">
                <CombatGrid participants={onGridParticipants} isGM={isGM} onTokenMove={() => {}} activeParticipantId={activeParticipant?.id} showMovementFor={selectedAction.type === 'MOVE' && isMyTurn ? activeParticipant : null} />
                {sessionData.current_mode === 'staging' && isGM && offGridParticipants.length > 0 && (
                  <div className="token-shelf">
                    <h4>Available Tokens</h4>
                    {offGridParticipants.map(p => (<div key={p.id} className="token-on-shelf" draggable onDragStart={(e) => e.dataTransfer.setData("participantId", p.id)}><Token participant={p} /></div>))}
                  </div>
                )}
              </div>
            )}
            
          </Panel>
        </div>

        <div key="context">
          <Panel title="Context" onToggleCollapse={() => togglePanelCollapse('context')}>
            {sessionData.current_mode === 'combat' ? (
                <>
                    <InitiativeTracker participants={sessionData.participants} turnOrder={sessionData.turn_order} currentTurnIndex={sessionData.current_turn_index} />
                    <ActionPanel abilities={activeCharacterAbilities} isMyTurn={isMyTurn} activeParticipant={activeParticipant} selectedAction={selectedAction} turnActions={turnActions} onSelectMove={() => {}} onSelectAbility={() => {}} onEndTurn={handleEndTurn}/>
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