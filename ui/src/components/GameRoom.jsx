// ui/src/components/GameRoom.jsx

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import GridLayout from 'react-grid-layout';
import CombatGrid from './CombatGrid';
import InitiativeTracker from './InitiativeTracker';
import ActionPanel from './ActionPanel';
import GameLog from './GameLog';
import CharacterCard from './CharacterCard';
import Panel from './Panel';
import Token from './Token';

function GameRoom({ sessionData, currentUser, isGM }) {
  const [selectedAction, setSelectedAction] = useState({ type: 'none', ability: null });
const [layout, setLayout] = useState([
    { i: 'avatars', x: 0, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
    { i: 'log', x: 9, y: 0, w: 3, h: 10, minW: 2, minH: 4 },
    { i: 'actions', x: 0, y: 4, w: 3, h: 6, minW: 2, minH: 4 },
    { i: 'grid', x: 3, y: 0, w: 6, h: 10, minW: 4, minH: 6 },
  ]);
  const originalLayouts = useRef({});
const [collapsedPanels, setCollapsedPanels] = useState({
      avatars: false,
      log: false,
      actions: false,
      grid: false,
  });

  const handleLayoutChange = (newLayout) => {
    const isResizingOrDragging = newLayout.some(item => item.isDraggable || item.isResizable);
    if (!isResizingOrDragging) {
        setLayout(newLayout);
    }
  };

  const togglePanelCollapse = (panelId) => {
    // 1. Determine the new state based on the current 'collapsedPanels' state.
    // We use the functional update form for safety, even though it's technically 
    // outside the scope of this setLayout dependency issue.
    setCollapsedPanels(prev => {
        const isCurrentlyCollapsed = prev[panelId];
        const willBeCollapsed = !isCurrentlyCollapsed;

        // 2. Queue the layout update using the *derived* new state (willBeCollapsed)
        setLayout(currentLayout => {
          const panelIndex = currentLayout.findIndex(item => item.i === panelId);
          if (panelIndex === -1) return currentLayout;
          
          const newLayout = [...currentLayout];
          const panelLayout = newLayout[panelIndex];
          
          if (willBeCollapsed) { // Collapse it: New height is 1
            // Save the current expanded height *before* collapsing it.
            originalLayouts.current[panelId] = panelLayout.h;
            newLayout[panelIndex] = { ...panelLayout, h: 1, minH: 1 };
          } else { // Expand it: Restore original height
            const originalHeight = originalLayouts.current[panelId] || 4;
            
            // Re-find the original minH for proper grid resizing
            const initialLayoutItem = [ 
                { i: 'avatars', minH: 3 }, 
                { i: 'log', minH: 4 }, 
                { i: 'actions', minH: 4 }, 
                { i: 'grid', minH: 6 }
            ].find(l => l.i === panelId);

            const originalMinHeight = initialLayoutItem ? initialLayoutItem.minH : 2;

            newLayout[panelIndex] = { ...panelLayout, h: originalHeight, minH: originalMinHeight };
          }
          return newLayout;
        });

        // 3. Return the new collapsedPanels state
        return {
            ...prev,
            [panelId]: willBeCollapsed,
        };
    });
  };
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
    <div className="game-room-dynamic">
      <GridLayout
        className="layout"
        layout={layout}
        cols={12}
        rowHeight={60} // Increased row height for better vertical space
        width={1920}
        onLayoutChange={handleLayoutChange}
        draggableHandle=".panel-header"
      >
        {/* Panel 1: Your Character Avatars */}
        <div key="avatars">
          <Panel title="Party" isCollapsed={collapsedPanels.avatars} onToggleCollapse={() => togglePanelCollapse('avatars')}>
            <div className="participants-grid-horizontal">
              {sessionData.participants.map((p) => (
                <CharacterCard key={p.id} participant={p} />
              ))}
            </div>
          </Panel>
        </div>
        
        {/* Panel 2: Your Game Log */}
        <div key="log">
          <Panel title="Game Log" isCollapsed={collapsedPanels.log} onToggleCollapse={() => togglePanelCollapse('log')}>
            <GameLog messages={sessionData.log || []} />
          </Panel>
        </div>

        {/* Panel 3: Your Actions / Initiative */}
        <div key="actions">
          <Panel title={sessionData.current_mode === 'combat' ? 'Combat Actions' : 'Initiative'} isCollapsed={collapsedPanels.actions} onToggleCollapse={() => togglePanelCollapse('actions')}>
            {sessionData.current_mode === 'combat' ? (
              <ActionPanel abilities={activeCharacterAbilities} isMyTurn={isMyTurn} activeParticipant={activeParticipant} selectedAction={selectedAction} turnActions={turnActions} onSelectMove={() => setSelectedAction({ type: 'MOVE' })} onSelectAbility={(ability) => setSelectedAction({ type: 'TARGETING', ability })} onEndTurn={() => {}}/>
            ) : (
              <InitiativeTracker participants={sessionData.participants} turnOrder={sessionData.turn_order} currentTurnIndex={sessionData.current_turn_index} />
            )}
          </Panel>
        </div>

        {/* Panel 4: Your Combat Grid and GM Controls */}
        <div key="grid">
          <Panel title="The World" isCollapsed={collapsedPanels.grid} onToggleCollapse={() => togglePanelCollapse('grid')}>
             {/* GM buttons will appear here based on game mode */}
            <CombatGrid participants={onGridParticipants} isGM={isGM} showMovementFor={selectedAction.type === 'MOVE' && isMyTurn ? activeParticipant : null} />
          </Panel>
        </div>
      </GridLayout>
    </div>
  );
}

export default GameRoom;