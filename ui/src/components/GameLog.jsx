// ui/src/components/GameLog.jsx

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

/**
 * Formats a log entry for display
 * @param {Object} entry - The log entry from the backend
 * @param {Array} participants - Array of session participants
 * @returns {JSX.Element|string} Formatted log message
 */
const formatLogEntry = (entry, participants = []) => {
    // Safe participant lookup
    const participantMap = new Map(participants.map(p => [p.id, p]));
    const actor = entry.actor_id ? participantMap.get(entry.actor_id) : null;
    const target = entry.target_id ? participantMap.get(entry.target_id) : null;
    
    // Safe detail extraction with defaults
    const details = entry.details || {};
    const actorName = actor?.character?.name || details.actor_name || 'Someone';
    const targetName = target?.character?.name || details.target_name || 'Someone';
    
    // Helper functions
    const formatPos = (pos) => pos ? `(${pos.x}, ${pos.y})` : 'unknown location';
    const safeGet = (obj, key, defaultVal = 'N/A') => obj?.[key] ?? defaultVal;

    switch (entry.event_type) {
        // ===== SESSION EVENTS =====
        case 'player_join':
            return <span className="log-system">--- {safeGet(details, 'player_name')} has joined the session. ---</span>;
        
        case 'character_select':
            return <span className="log-system">--- {safeGet(details, 'player_name')} has chosen to play as {safeGet(details, 'character_name')}. ---</span>;
        
        case 'character_deselection':
    return (
        <span className="log-system">
            <strong>{safeGet(details, 'player_name')}</strong> deselected <strong>{safeGet(details, 'character_name')}</strong>.
        </span>
    );
        
        case 'mode_change':
            return <span className="log-system">--- The GM has changed the game mode to {safeGet(details, 'new_mode', 'unknown').toUpperCase()}. ---</span>;

        // ===== MOVEMENT & POSITIONING =====
        case 'move':
            return (
                <span>
                    <strong>{actorName}</strong> moves to {formatPos(details.new_pos)}.
                </span>
            );
        
        case 'teleport':
            const distance = details.distance ? ` (${details.distance} squares)` : '';
            const status = details.status_applied ? ` and gained ${details.status_applied}` : '';
            return (
                <span className="log-entry teleport">
                    <strong className="actor">{actorName}</strong> used <strong>{safeGet(details, 'ability_name')}</strong> to move from {formatPos(details.old_pos)} to {formatPos(details.new_pos)}{distance}{status}.
                </span>
            );
        
        case 'token_place':
            return (
                <span className="log-gm-action">
                    The GM placed <strong>{safeGet(details, 'character_name')}</strong> on the grid at {formatPos(details.pos)}.
                </span>
            );
        
        case 'token_move':
            return (
                <span className="log-gm-action">
                    The GM moved <strong>{safeGet(details, 'character_name')}</strong> to {formatPos(details.pos)}.
                </span>
            );

        // ===== COMBAT ACTIONS =====
        case 'attack_hit':
            const { roll = 0, modifier = 0, total = 0, dc = 0, damage = 0 } = details;
            return (
                <span>
                    <strong>{actorName}</strong>'s <strong>{safeGet(details, 'ability_name')}</strong> <span className="log-hit">hits</span> <strong>{targetName}</strong>! 
                    {' '}(<span className="log-dice">Roll: {roll} + Mod: {modifier} = {total}</span> vs DC {dc}). 
                    Deals <span className="log-damage">{damage} damage</span>.
                </span>
            );
        
        case 'attack_miss':
            const { 
                roll: missRoll = 0, 
                modifier: missMod = 0, 
                total: missTotal = 0, 
                dc: missDc = 0 
            } = details;
            return (
                <span>
                    <strong>{actorName}</strong>'s <strong>{safeGet(details, 'ability_name')}</strong> <span className="log-miss">misses</span> <strong>{targetName}</strong>. 
                    {' '}(<span className="log-dice">Roll: {missRoll} + Mod: {missMod} = {missTotal}</span> vs DC {missDc})
                </span>
            );
        
        case 'out_of_range':
            return (
                <span className="log-warning">
                    <strong>{actorName}</strong>'s <strong>{safeGet(details, 'ability_name')}</strong> fails: <strong>{targetName}</strong> is out of range.
                </span>
            );

        // ===== HEALING =====
        case 'heal':
        case 'heal_from_item':
            return (
                <span className="log-entry heal">
                    <strong className="actor">{actorName}</strong> healed <strong className="target">{targetName}</strong> for <span className="log-healing">{safeGet(details, 'healing')} Prana</span>.
                </span>
            );

        // ===== STATUS CHANGES =====
        case 'status_change':
            return (
                <span className="log-status">
                    --- <strong>{safeGet(details, 'character_name')}</strong> is now <span className="log-status-value">{safeGet(details, 'new_status', 'unknown').toUpperCase()}</span>! ---
                </span>
            );

        // ===== INITIATIVE =====
        case 'initiative_roll':
            const { 
                character_name = 'Unknown', 
                roll: initiativeRoll = 0, 
                modifier: initiativeModifier = 0, 
                total: initiativeTotal = 0 
            } = details;
            return (
                <span>
                    <strong>{character_name}</strong> rolls <span className="log-dice">({initiativeRoll})</span> + Dakṣatā Mod ({initiativeModifier}) for a total of <span className="log-total">{initiativeTotal}</span> for initiative.
                </span>
            );
        
        case 'turn_order_set':
            return (
                <span className="log-system">
                    --- The turn order is set: {safeGet(details, 'order')}. ---
                </span>
            );

        // ===== SKILL CHECKS =====
        case 'skill_check_initiated':
            const targetNames = Array.isArray(details.target_names) ? details.target_names.join(', ') : 'targets';
            return (
                <span className="log-skill-check">
                    <strong>{safeGet(details, 'actor_name')}</strong> requests a <strong>{safeGet(details, 'check_type')}</strong> check (DC {safeGet(details, 'dc', 0)}) for{' '}
                    <strong>{targetNames}</strong>: <em>"{safeGet(details, 'description', 'No description')}"</em>
                </span>
            );
        
        case 'skill_check_result':
            const { 
                character_name: charName = 'Unknown',
                check_type = 'unknown',
                roll: skillRoll = 0,
                modifier: skillMod = 0,
                total: skillTotal = 0,
                dc: skillDc = 0,
                success = false,
                advantage_used = false,
                roll_breakdown = ''
            } = details;
            const resultClass = success ? 'log-success' : 'log-failure';
            const advantageText = advantage_used ? ` (Advantage: ${roll_breakdown})` : '';
            const tooltipText = `Roll: ${skillRoll}${advantageText} + Mod: ${skillMod}`;
            
            return (
                <span>
                    <strong>{charName}</strong> attempts a <strong>{check_type}</strong> check:{' '}
                    <strong className="roll-tooltip" title={tooltipText}>
                        Total {skillTotal}
                    </strong>
                    {' '}(DC {skillDc}) - <strong className={resultClass}>{success ? 'Success!' : 'Failure.'}</strong>
                </span>
            );

        // ===== ITEM ACTIONS =====
        case 'gm_give_item':
            return (
                <span className="log-item">
                    The Game Master gives <strong>{safeGet(details, 'item_name')} (x{safeGet(details, 'quantity', 1)})</strong> to <strong>{safeGet(details, 'character_name')}</strong>.
                </span>
            );
        
        case 'item_use':
            return (
                <span className="log-item">
                    <strong>{safeGet(details, 'character_name')}</strong> uses a <strong>{safeGet(details, 'item_name')}</strong>.
                </span>
            );
        
        case 'item_destroy':
            return (
                <span className="log-item-destroy">
                    <strong>{safeGet(details, 'character_name')}</strong> destroys their <strong>{safeGet(details, 'item_name')}</strong>.
                </span>
            );
        
        case 'item_give':
            return (
                <span className="log-item">
                    <strong>{safeGet(details, 'giver_name')}</strong> gives <strong>{safeGet(details, 'item_name')} (x{safeGet(details, 'quantity', 1)})</strong> to <strong>{safeGet(details, 'receiver_name')}</strong>.
                </span>
            );
        
        case 'item_equip':
            const equipAction = details.equipped ? 'equips' : 'unequips';
            return (
                <span className="log-item">
                    <strong>{safeGet(details, 'character_name')}</strong> {equipAction} their <strong>{safeGet(details, 'item_name')}</strong>.
                </span>
            );

        // ===== ENVIRONMENTAL OBJECTS =====
        case 'environmental_object_created':
            return (
                <span className="log-environmental">
                    --- The GM created <strong>{safeGet(details, 'object_name')}</strong> ({safeGet(details, 'object_type')}) with {safeGet(details, 'integrity', 0)} integrity. ---
                </span>
            );
        
        case 'environmental_object_damaged':
            const remainingIntegrity = safeGet(details, 'remaining_integrity', 0);
            const damageAmount = safeGet(details, 'damage', 0);
            return (
                <span className="log-environmental-damage">
                    <strong>{safeGet(details, 'object_name')}</strong> takes <span className="log-damage">{damageAmount} damage</span>! 
                    {' '}(Integrity: <strong>{remainingIntegrity}</strong>)
                </span>
            );
        
        case 'environmental_object_repaired':
            const newIntegrity = safeGet(details, 'new_integrity', 0);
            const repairAmount = safeGet(details, 'repair_amount', 0);
            return (
                <span className="log-environmental-repair">
                    <strong>{safeGet(details, 'object_name')}</strong> is repaired by <span className="log-healing">{repairAmount} integrity</span>! 
                    {' '}(Integrity: <strong>{newIntegrity}</strong>)
                </span>
            );
        
        case 'environmental_object_destroyed':
            return (
                <span className="log-environmental-destroyed">
                    💥 <strong>{safeGet(details, 'object_name')}</strong> has been <strong className="log-destroyed">DESTROYED</strong>! 💥
                </span>
            );
        
        case 'environmental_section_damaged':
            return (
                <span className="log-environmental-damage">
                    Section {safeGet(details, 'section_number', 0)} of <strong>{safeGet(details, 'object_name')}</strong> takes <span className="log-damage">{safeGet(details, 'damage', 0)} damage</span>! 
                    {' '}(Section integrity: <strong>{safeGet(details, 'section_integrity', 0)}</strong>)
                </span>
            );
        
        case 'environmental_section_collapsed':
            return (
                <span className="log-environmental-destroyed">
                    ⚠️ Section {safeGet(details, 'section_number', 0)} of <strong>{safeGet(details, 'object_name')}</strong> has <strong className="log-collapsed">COLLAPSED</strong>! ⚠️
                </span>
            );

        // ===== CAMPAIGN SYSTEM =====
        case 'campaign_selected':
            return (
                <span className="log-system">
                    --- GM selected campaign: <strong>{safeGet(details, 'campaign_name')}</strong> ---
                </span>
            );
        
        case 'character_selection':
            return (
                <span className="log-system">
                    <strong>{safeGet(details, 'player_name')}</strong> selected <strong>{safeGet(details, 'character_name')}</strong>.
                </span>
            );
        
        case 'scene_change':
            return (
                <span className="log-system">
                    --- Scene changed to: <strong>{safeGet(details, 'scene_name')}</strong> ---
                </span>
            );

        // ===== LOKA SYSTEM (Future) =====
        case 'loka_resonance_changed':
            return (
                <span className="log-loka">
                    ✨ The Loka resonance shifts to <strong>{safeGet(details, 'new_resonance', 'unknown').toUpperCase()}</strong>! ✨
                </span>
            );
        
        case 'loka_avahana_activated':
            return (
                <span className="log-loka">
                    🌟 <strong>{safeGet(details, 'character_name')}</strong> activates <strong>Loka Āvāhana</strong>, summoning the power of <strong>{safeGet(details, 'loka', 'unknown')}</strong>! 🌟
                </span>
            );

        // ===== FALLBACK =====
        default:
            console.warn('Unknown log event type:', entry.event_type, details);
            return (
                <span className="log-unknown">
                    Unknown event: {entry.event_type} {details ? `(${JSON.stringify(details)})` : ''}
                </span>
            );
    }
};

/**
 * GameLog Component
 * Displays all game events in chronological order
 */
function GameLog({ sessionId, participants = [], newLogTrigger }) {
    const [logEntries, setLogEntries] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const logEndRef = useRef(null);

    const fetchLog = async () => {
        if (!sessionId) return;
        
        setIsLoading(true);
        setError(null);
        
        try {
            const res = await axios.get(`http://localhost:8000/sessions/${sessionId}/log`);
            setLogEntries(res.data || []);
        } catch (err) {
            console.error("Failed to fetch game log", err);
            setError("Failed to load game log");
        } finally {
            setIsLoading(false);
        }
    };

    // Fetch log on mount and when triggered
    useEffect(() => {
        fetchLog();
    }, [sessionId, newLogTrigger]);

    // Auto-scroll to bottom
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logEntries]);

    if (!sessionId) {
        return (
            <div className="game-log">
                <div className="log-messages-container">
                    <p className="placeholder-text">No session selected</p>
                </div>
            </div>
        );
    }

    return (
        <div className="game-log">
            <div className="log-messages-container">
                {isLoading && logEntries.length === 0 && (
                    <p className="placeholder-text">Loading log...</p>
                )}
                
                {error && (
                    <p className="log-error">{error}</p>
                )}
                
                {logEntries.length === 0 && !isLoading && !error && (
                    <p className="placeholder-text">No events yet. The adventure begins...</p>
                )}
                
                {logEntries.map(entry => (
                    <p key={entry.id} className={`log-message log-type-${entry.event_type}`}>
                        {formatLogEntry(entry, participants)}
                    </p>
                ))}
                
                <div ref={logEndRef} />
            </div>
        </div>
    );
}

export default GameLog;