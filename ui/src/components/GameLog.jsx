// ui/src/components/GameLog.jsx (Refactored)

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// --- NEW: The Log Formatting Helper ---
const formatLogEntry = (entry, participants) => {
    const participantMap = new Map(participants.map(p => [p.id, p]));
    const actor = entry.actor_id ? participantMap.get(entry.actor_id) : null;
    const target = entry.target_id ? participantMap.get(entry.target_id) : null;
    const actorName = actor?.character.name || entry.details.actor_name || 'Someone';
    const targetName = target?.character.name || entry.details.target_name || 'Someone';

    switch (entry.event_type) {
        case 'player_join':
            return `--- ${entry.details.player_name} has joined the session. ---`;
        case 'character_select':
            return `--- ${entry.details.player_name} has chosen to play as ${entry.details.character_name}. ---`;
        case 'move':
            return `${actorName} moves to (${entry.details.new_pos.x}, ${entry.details.new_pos.y}).`;
        case 'token_place':
            return `The GM placed ${entry.details.character_name} on the grid at (${entry.details.pos.x}, ${entry.details.pos.y}).`;
        case 'token_move':
            return `The GM moved ${entry.details.character_name} to (${entry.details.pos.x}, ${entry.details.pos.y}).`;
        case 'attack_hit':
            const { roll, modifier, total, dc, damage } = entry.details;
            return (
                <span>
                    {actorName}'s {entry.details.ability_name} <span className="log-hit">hits</span> {targetName}! 
                    (<span className="log-dice">Roll: {roll} + Mod: {modifier} = {total}</span> vs DC {dc}). 
                    Deals <span className="log-damage">{damage} damage</span>.
                </span>
            );
        case 'attack_miss':
             const { roll: missRoll, modifier: missMod, total: missTotal, dc: missDc } = entry.details;
            return (
                <span>
                    {actorName}'s {entry.details.ability_name} <span className="log-miss">misses</span> {targetName}. 
                    {' '}(<span className="log-dice">Roll: {missRoll} + Mod: {missMod} = {missTotal}</span> vs DC {missDc})
                </span>
            );
        case 'out_of_range':
            return `${actorName}'s ${entry.details.ability_name} fails: ${targetName} is out of range.`;
        case 'mode_change':
            return `--- The GM has changed the game mode to ${entry.details.new_mode.toUpperCase()}. ---`;
        case 'status_change': // Also adding the formatter for this
             return `--- ${entry.details.character_name} is now ${entry.details.new_status.toUpperCase()}! ---`;
        case 'initiative_roll':
            const { character_name, roll: initiativeRoll, modifier: initiativeModifier, total:initiativeTotal } = entry.details;
            return (
                <span>
                    {character_name} rolls <span className="log-dice">({initiativeRoll})</span> + Dakṣatā Mod ({initiativeModifier}) for a total of <span className="log-total">{initiativeTotal}</span> for initiative.
                </span>
            );
        case 'skill_check_initiated':
        return (
          <span>
            <strong>{entry.details.actor_name}</strong> requests a <strong>{entry.details.check_type}</strong> check (DC {entry.details.dc}) for{' '}
            <strong>{(entry.details.target_names || []).join(', ')}</strong>: <em>"{entry.details.description}"</em>
          </span>
        );
        case 'skill_check_result':
        // Destructure all the needed properties from entry.details
        const { character_name : char_name, check_type, roll : skill_roll, modifier: skill_mod, total : skill_total, dc: skill_dc, success, advantage_used, roll_breakdown } = entry.details;
        const resultClass = success ? 'log-success' : 'log-failure';
        const advantageText = advantage_used ? ` (Advantage: ${roll_breakdown})` : '';
        const tooltipText = `Roll: ${skill_roll}${advantageText} + Mod: ${skill_mod}`;
        
        return (
          <span>
            <strong>{char_name}</strong> attempts a <strong>{check_type}</strong> check:{' '}
            <strong className="roll-tooltip" title={tooltipText}>
              Total {skill_total}
            </strong>
            {' '}(DC {skill_dc}) - <strong className={resultClass}>{success ? 'Success!' : 'Failure.'}</strong>
          </span>
        );
        case 'turn_order_set':
            return <span className="log-system">--- The turn order is set: {entry.details.order}. ---</span>;
        default:
            return `Unknown event: ${entry.event_type}`;
    }
};

function GameLog({ sessionId, participants, newLogTrigger }) {
    const [logEntries, setLogEntries] = useState([]);
    const logEndRef = useRef(null);

    const fetchLog = () => {
        axios.get(`http://localhost:8000/sessions/${sessionId}/log`)
            .then(res => setLogEntries(res.data))
            .catch(err => console.error("Failed to fetch game log", err));
    };

    // Fetch log on initial component mount and when triggered by a new entry
    useEffect(() => {
        if (sessionId) {
            fetchLog();
        }
    }, [sessionId, newLogTrigger]);

    // Auto-scroll to the bottom of the log
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logEntries]);

    return (
        <div className="game-log">
            <div className="log-messages-container">
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