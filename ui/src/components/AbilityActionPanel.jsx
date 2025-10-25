// ui/src/components/AbilityActionPanel.jsx
// Replace your existing ActionPanel with this enhanced version

import React, { useState, useCallback, useEffect } from 'react';

function AbilityActionPanel({ 
  abilities, 
  isMyTurn, 
  activeParticipant, 
  sessionId,
  onEndTurn,
  participants,
  onActionComplete ,
  onSetGridTargeting,
  onSetParticipantTargeting,
  cleanupRef
}) {
  const [selectedAbility, setSelectedAbility] = useState(null);
  const [targetingMode, setTargetingMode] = useState(null);
  const [error, setError] = useState('');
    const clearTargetingState = useCallback(() => {
        setSelectedAbility(null);
        setTargetingMode(null);
        setError('');
    }, []);
    useEffect(() => {
        if (cleanupRef) {
            cleanupRef.current = clearTargetingState;
        }
        // Cleanup function for the ref, though usually not strictly necessary for this use case
        return () => {
            if (cleanupRef) {
                cleanupRef.current = null;
            }
        };
    }, [cleanupRef, clearTargetingState]);
  if (!isMyTurn) {
    return (
      <div className="action-panel">
        <h4>Actions</h4>
        <p>Waiting for another player...</p>
      </div>
    );
  }

  const isDowned = activeParticipant?.status === 'downed';

  if (isDowned) {
    return (
      <div className="action-panel">
        <h4>Your Turn!</h4>
        <p style={{ color: '#ff6b6b', fontWeight: 'bold' }}>You are downed!</p>
      </div>
    );
  }

  const handleAbilityClick = (ability) => {
    setError('');
    setSelectedAbility(ability);
    if (onSetGridTargeting) onSetGridTargeting(null);
    if (onSetParticipantTargeting) onSetParticipantTargeting(null);
    if (ability.target_type === 'self') {
      executeAbility(ability, { participant_id: activeParticipant.id });
    } else if (ability.target_type === 'ground') {
      setTargetingMode('ground');
      if (onSetGridTargeting) {
          onSetGridTargeting(ability); 
      }
    } else {
      setTargetingMode('participant');
      if (onSetParticipantTargeting) {
                onSetParticipantTargeting(ability);
            }
    }
  };
    const handleGridTarget = (x, y) => {
    if (targetingMode === 'ground' && selectedAbility) {
        // The target object contains the x, y coordinates
        executeAbility(selectedAbility, { x: x, y: y }); 
    }
  };
  const executeAbility = async (ability, target) => {
    try {
      const payload = {
        actor_id: activeParticipant.id,
        ability_id: ability.id,
        primary_target: target,
        secondary_targets: []
      };

      // Use fetch instead of axios for artifact compatibility
      const response = await fetch(
        `http://localhost:8000/sessions/${sessionId}/ability`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Action failed');
      }

      if (onActionComplete) {
        onActionComplete();
      }
    } catch (err) {
      setError(err.message);
      console.error('Ability execution failed:', err);
    }
  };

  const canUseAbility = (ability) => {
    if (!activeParticipant) return false;

    if (ability.action_type === 'action' && activeParticipant.actions < 1) return false;
    if (ability.action_type === 'bonus action' && activeParticipant.bonus_actions < 1) return false;
    if (ability.action_type === 'reaction' && activeParticipant.reactions < 1) return false;

    if (ability.resource_type === 'tapas' && activeParticipant.current_tapas < ability.resource_cost) return false;
    if (ability.resource_type === 'maya' && activeParticipant.current_maya < ability.resource_cost) return false;
    if (ability.resource_type === 'speed' && activeParticipant.remaining_speed < ability.resource_cost) return false;

    return true;
  };

  const getAbilityTooltip = (ability) => {
    let tooltip = ability.description || '';
    tooltip += `\n\nAction: ${ability.action_type}`;
    if (ability.resource_cost > 0) tooltip += `\nCost: ${ability.resource_cost} ${ability.resource_type}`;
    tooltip += `\nRange: ${ability.range}`;
    if (ability.effect_radius > 0) tooltip += `\nAoE: ${ability.effect_radius}`;
    if (ability.damage_dice) tooltip += `\nDice: ${ability.damage_dice}`;
    return tooltip;
  };

  return (
    <div className="ability-action-panel">
      <div className="panel-header">
        <h4>Your Turn</h4>
        <div className="action-economy">
          <span title="Actions">⚔️ {activeParticipant.actions}</span>
          <span title="Bonus Actions">⚡ {activeParticipant.bonus_actions}</span>
          <span title="Reactions">🛡️ {activeParticipant.reactions}</span>
          <span title="Movement">👟 {activeParticipant.remaining_speed}</span>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {targetingMode && (
        <div className="targeting-prompt">
          <p>
            {targetingMode === 'participant' 
              ? `🎯 Select a target for ${selectedAbility.name}` 
              : `📍 Click grid for ${selectedAbility.name}`}
          </p>
          <button onClick={() => { clearTargetingState();
            if (onSetGridTargeting) onSetGridTargeting(null);
            if (onSetParticipantTargeting) onSetParticipantTargeting(null);
          }}>
            Cancel
          </button>
        </div>
      )}

      <div className="abilities-grid">
        {Array.isArray(abilities) && abilities.map(ability => (
          <div
            key={ability.id}
            className={`ability-card ${!canUseAbility(ability) ? 'disabled' : ''} ${selectedAbility?.id === ability.id ? 'selected' : ''}`}
            onClick={() => canUseAbility(ability) && handleAbilityClick(ability)}
            title={getAbilityTooltip(ability)}
          >
            <div className="ability-name">{ability.name}</div>
            <div className="ability-footer">
              <span>{ability.action_type === 'action' ? '⚔️' : ability.action_type === 'bonus action' ? '⚡' : '🛡️'}</span>
              {ability.resource_cost > 0 && <span className="cost-badge">{ability.resource_cost}</span>}
              {ability.range > 0 && <span className="range-badge">📏{ability.range}</span>}
            </div>
          </div>
        ))}
      </div>
      <button className="end-turn-button" onClick={onEndTurn}>End Turn</button>
    </div>
  );
}

export default AbilityActionPanel;

