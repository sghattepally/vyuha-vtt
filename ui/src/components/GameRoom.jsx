import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import GridLayout from 'react-grid-layout';
import Panel from './Panel';
import CombatGrid from './CombatGrid';
import InitiativeTracker from './InitiativeTracker';
import AbilityActionPanel from './AbilityActionPanel';
import GameLog from './GameLog';
import SkillCheckModal from './SkillCheckModal';
import SkillCheckPrompt from './SkillCheckPrompt';
import CharacterSheet from './CharacterSheet';
import InventoryPanel from './InventoryPanel';
import EnvironmentalObjectPanel from './EnvironmentalObjectPanel';
import Token from './Token';
import NpcManager from './NpcManager';
import PartyPanel from './PartyPanel';
import AttributeSkillPanel from './AttributeSkillPanel';
import GiveItemModal from './GiveItemModal';

const initialLayout = [
  { i: 'party', x: 3, y: 0, w: 3, h: 4, minW: 3, minH: 3 },
  { i: 'log', x: 6, y: 0, w: 5, h: 4, minW: 2, minH: 3 },
  { i: 'main', x: 3, y: 4, w: 8, h: 7, minW: 4, minH: 5 },
  { i: 'context', x: 0, y: 0, w: 3, h: 11, minW: 2, minH: 5 },
];
const COLLAPSED_HEIGHT = 1;
function GameRoom({ sessionData, currentUser, isGM, isGmOverride, dragPreviewRef , newLogTrigger }) {
  const [gridTargetAbility, setGridTargetAbility] = useState(null);
  const [selectedAction, setSelectedAction] = useState({ type: 'none', ability: null });
  const [activeCharacterAbilities, setActiveCharacterAbilities] = useState([]);
  const [turnActions, setTurnActions] = useState({ hasAttacked: false });
  const abilityPanelCleanupRef = useRef(null);
  const [isNpcManagerOpen, setIsNpcManagerOpen] = useState(false);
  const [isSkillCheckModalOpen, setIsSkillCheckModalOpen] = useState(false);
  const [isGiveItemModalOpen, setIsGiveItemModalOpen] = useState(false);
  const [acknowledgedCheckId, setAcknowledgedCheckId] = useState(() => {
    const saved = localStorage.getItem('acknowledgedChecks');
    return saved ? JSON.parse(saved) : [];
  });
  useEffect(() => {
    localStorage.setItem('acknowledgedChecks', JSON.stringify(acknowledgedCheckId));
  }, [acknowledgedCheckId]);
  const [mainPanelTab, setMainPanelTab] = useState('world');
  
  const [layout, setLayout] = useState(initialLayout);
  const originalLayouts = useRef({});
  const effectiveIsGM = isGM && isGmOverride;
  const handleLayoutChange = (newLayout) => {
    setLayout(newLayout);
  };
  const mainPanelTabs = [
    { key: 'world', label: 'World' },
    { key: 'inventory', label: 'Inventory'},
    { key: 'sheet', label: 'Character Sheet' },
    { key: 'journal', label: 'Journal' },
  ];

  const renderMainPanelContent = () => {
    switch (mainPanelTab) {
      case 'inventory':
        return <InventoryPanel character={displayCharacter} participants={sessionData.participants}/>;

      case 'sheet':
        return <CharacterSheet character={displayCharacter} />;

      case 'journal':
        return <div className="placeholder-text">Journal and notes will appear here.</div>;

      case 'world':
      default: 
        if (sessionData.current_mode === 'combat' || sessionData.current_mode === 'staging') {
          return (
            <div className="staging-layout">
              <div className="grid-container">
                <CombatGrid
                  participants={onGridParticipants}
                  isGM={isGM}
                  onTokenMove={handleTokenMove}
                  onGridClick={handleGridClick}
                  onTokenClick={handleTokenClick}
                  activeParticipantId={activeParticipant?.id}
                  showMovementFor={selectedAction.type === 'MOVE' && isMyTurn ? activeParticipant : null}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const participantId = e.dataTransfer.getData("participantId");
                    const gridRect = e.currentTarget.getBoundingClientRect();
                    const x = Math.floor((e.clientX - gridRect.left) / 50);
                    const y = Math.floor((e.clientY - gridRect.top) / 50);
                    if (participantId) {
                      handleTokenMove(participantId, x, y);
                    }
                  }}
                />
              </div>
            </div>
          );
        } else { // Exploration mode
          return (
            <div className="exploration-view">
              <p>Exploration mode - world view will appear here.</p>
            </div>
          );
        }
    }
  };
const handleGiveItem = async (payload) => {
    try {
      await axios.post('http://localhost:8000/gm/give-item', payload);
      setIsGiveItemModalOpen(false); // Close modal on success
      // The websocket will handle updating the player's inventory view
    } catch (error) {
      console.error("Failed to give item:", error);
      alert("Failed to give item. See console for details.");
    }
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


  const handleRequestSkillCheck = async (payload) => {
    try {
      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/skill_check/request`, payload);
      setIsSkillCheckModalOpen(false); // Close modal on successful request
    } catch (error) {
      console.error("Failed to request skill check:", error.response?.data?.detail || error.message);
      alert('Failed to request skill check. See console for details.');
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
  const currentUserParticipant = sessionData.participants.find(p => p.player_id === currentUser.id);
  
  const displayCharacter = currentUserParticipant?.character;
  const handleGridClick = async (x, y) => {
  if (gridTargetAbility && activeParticipant && isMyTurn) {
    try {
      const payload = {
        actor_id: activeParticipant.id,
        ability_id: gridTargetAbility.id,
        primary_target: { x: x, y: y },
        secondary_targets: [],
      };

      await axios.post(`http://localhost:8000/sessions/${sessionData.id}/ability`, payload);
      
      setGridTargetAbility(null);
      
    } catch (err) {
      console.error("Ground-targeted ability failed:", err.response?.data?.detail || err);
      setGridTargetAbility(null);
    }
  }
};
  const [participantTargetAbility, setParticipantTargetAbility] = useState(null);
  const handleSetParticipantTargeting = (ability) => {
    console.log("DEBUG_FE: SETTING PARTICIPANT TARGET ABILITY:", ability?.name);
    setParticipantTargetAbility(ability);
};
const handleTokenClick = async (targetId) => {
    if (participantTargetAbility && activeParticipant && isMyTurn) {
        if (targetId === activeParticipant.id && participantTargetAbility.target_type !== 'self') {
             return; 
        }

        try {
            const payload = {
                actor_id: activeParticipant.id,
                ability_id: participantTargetAbility.id,
                primary_target: { participant_id: targetId }, // Target is a participant ID
                secondary_targets: [],
            };

            await axios.post(`http://localhost:8000/sessions/${sessionData.id}/ability`, payload);
            setParticipantTargetAbility(null);
            if (abilityPanelCleanupRef.current) {
                abilityPanelCleanupRef.current();
            }
            
        } catch (err) {
            console.error("Player-targeted ability failed:", err.response?.data?.detail || err);
            // Don't clear state on error yet, let the user re-try or cancel
        }
    }
};
  const latestCheckForPlayer = sessionData.skill_checks
    ?.filter(check => check.participant_id === currentUserParticipant?.id)
    .sort((a, b) => b.id - a.id)[0]; // Get the most recent one

  
  const isPromptVisible = latestCheckForPlayer && latestCheckForPlayer.id !== acknowledgedCheckId;
  
  const handleAcknowledgeCheck = () => {
    if (latestCheckForPlayer) {
      setAcknowledgedCheckId(latestCheckForPlayer.id);
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
    {isSkillCheckModalOpen && (
        <SkillCheckModal
          sessionData={sessionData}
          participants={sessionData.participants}
          onClose={() => setIsSkillCheckModalOpen(false)}
          onSkillCheckRequested={handleRequestSkillCheck}
        />
      )}
      {isGiveItemModalOpen && (
        <GiveItemModal
          participants={sessionData.participants}
          onClose={() => setIsGiveItemModalOpen(false)}
          onGiveItem={handleGiveItem}
        />
      )}
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
          draggableCancel=".panel-header button"
        >
    {isPromptVisible && (
        <div key="skill_check" data-grid={{x: 0, y: 0, w: 3, h: 4}}>
          <h3 style={{ textAlign: 'center' }}>Skill Check</h3>
            <div title="Skill Check" canCollapse={false}>
                <SkillCheckPrompt
                  sessionData={sessionData}
                  check={latestCheckForPlayer}
                  onAcknowledge={handleAcknowledgeCheck}
                  participant={currentUserParticipant}
                />
            </div>
        </div>
    )}
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

          <div key="main" className="main-panel-wrapper">
            <Panel onCollapse={() => togglePanelCollapse('main')}
              isCollapsed={layout.find(p => p.i === 'main')?.h === COLLAPSED_HEIGHT}
              // Pass the new tab props
              tabs={mainPanelTabs}
              activeTab={mainPanelTab}
              onTabClick={setMainPanelTab}>
                {renderMainPanelContent()}


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
                      <button onClick={() => setIsSkillCheckModalOpen(true)}>Request Skill Check</button>
                      <button onClick={() => setIsGiveItemModalOpen(true)}>Give Item</button>
                    </>
                  )}
                  {sessionData.current_mode === 'staging' && (
                    <button onClick={handleBeginCombat}>Begin Combat</button>
                  )}
                  {(sessionData.current_mode === 'staging' || sessionData.current_mode === 'combat') && (
    <EnvironmentalObjectPanel 
        sessionId={sessionData.id}
        isGM={effectiveIsGM}
    />
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
                  <AbilityActionPanel
                      abilities={activeCharacterAbilities}
                      isMyTurn={isMyTurn}
                      activeParticipant={activeParticipant}
                      sessionId={sessionData.id}
                      participants={sessionData.participants}
                      onEndTurn={handleEndTurn}
                      onActionComplete={() => {
                      }}
                      onSetGridTargeting={(ability) => setGridTargetAbility(ability)}
                      onSetParticipantTargeting={handleSetParticipantTargeting}
                      cleanupRef={abilityPanelCleanupRef}
                    />
                </>
              ) : (
                currentUserParticipant && displayCharacter ? (
                <AttributeSkillPanel 
                    character={displayCharacter}
                    raceDetails={displayCharacter.race}
                    classDetails={displayCharacter.char_class}
                />
            ) : (
                <div className="placeholder-text">Character details will appear here.</div>
              ))}
            </Panel>
          </div>
        </GridLayout>
      </div>
    </>);
}

export default GameRoom;