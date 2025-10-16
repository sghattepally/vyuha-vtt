// ui/srcsrc/App.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import CharacterCard from './components/CharacterCard';
import CombatGrid from './components/CombatGrid';
import InitiativeTracker from './components/InitiativeTracker';
import ActionPanel from './components/ActionPanel';
import GameLog from './components/GameLog';
import './App.css';

const IS_GM = true;
const CURRENT_USER_ID = 2;

function App() {
    const [sessionData, setSessionData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedAction, setSelectedAction] = useState({ type: 'none', ability: null });
    const [activeCharacterAbilities, setActiveCharacterAbilities] = useState([]);
    const [turnActions, setTurnActions] = useState({ hasAttacked: false });

    const activeParticipant = sessionData?.turn_order?.length > 0 ? sessionData.participants.find(p => p.id === sessionData.turn_order[sessionData.current_turn_index]) : null;
    const isMyTurn = activeParticipant && (activeParticipant.character.owner_id === CURRENT_USER_ID || IS_GM);

    const fetchSessionData = async () => {
        try {
            const response = await axios.get('http://localhost:8000/sessions/1/');
            setSessionData(response.data);
        } catch (err) {
            setError('Failed to load. Is backend running & DB seeded?');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchSessionData(); }, []);

    
    useEffect(() => {
        if (activeParticipant) {
            const fetchAbilities = async () => {
                const res = await axios.get(`http://localhost:8000/characters/${activeParticipant.character.id}/abilities/`);
                setActiveCharacterAbilities(res.data);
            };
            fetchAbilities();
        }
    }, [activeParticipant]);
    
    
    useEffect(() => {
        // We don't want to connect until we have a session ID from our initial fetch.
        if (!sessionData?.id) return;

        // Construct the WebSocket URL. 'ws://' is the standard for non-secure WebSockets.
        const ws = new WebSocket(`ws://localhost:8000/ws/${sessionData.id}/${CURRENT_USER_ID}`);

        ws.onopen = () => {
            console.log("WebSocket connection established.");
        };

        // This is the most important part.
        // When the server broadcasts a message, this function is called.
        ws.onmessage = (event) => {
            console.log("Received update from server!");
            const updatedSessionData = JSON.parse(event.data);
            
            // This one line replaces the state with the new, authoritative state from the server.
            // This is now the ONLY place where sessionData should be updated after an action.
            setSessionData(updatedSessionData);
        };

        ws.onerror = (error) => {
            console.error("WebSocket Error:", error);
            setError("Live connection to server failed.");
        };

        ws.onclose = () => {
            console.log("WebSocket connection closed.");
        };

        // This is a "cleanup" function. React runs it when the component
        // unmounts to make sure we close the connection and prevent errors.
        return () => {
            ws.close();
        };

    
    }, [sessionData?.id]);
    

    const performAction = async (actionPayload) => {
        try {
            const response = await axios.post('http://localhost:8000/sessions/1/action', actionPayload);

            if (actionPayload.action_type === 'ATTACK') {
              setTurnActions(prev => ({ ...prev, hasAttacked: true }));
            }
        } catch (err) {
            const errorMsg = err.response?.data?.detail || "An unknown error occurred.";
            console.error("Action failed:", errorMsg);
        }
        setSelectedAction({ type: 'none', ability: null });
    };

    // --- All functions below are modified to remove manual setSessionData calls ---

    const handlePrepareForCombat = async () => {
        // We still make the request...
        await axios.patch('http://localhost:8000/sessions/1/', { current_mode: 'staging' });
        // ...but we DELETE the line that sets the state. The WebSocket will handle it.
        // const res = ...; setSessionData(res.data); // <-- DELETE
    };

    const handleBeginCombat = async () => {
        if (!IS_GM) return;
        try {
            await axios.post('http://localhost:8000/sessions/1/begin_combat');
            // setSessionData(response.data); // <-- DELETE
        } catch (err) {
            console.error("Failed to begin combat", err);
        }
    };
    
    const handleEndCombat = async () => {
        if (!IS_GM) return;
        try {
            await axios.patch('http://localhost:8000/sessions/1/', { current_mode: 'exploration' });
            // setSessionData(response.data); // <-- DELETE
        } catch (err) {
            console.error("Failed to end combat", err);
        }
    };
    
    const handleEndTurn = async () => {
        setSelectedAction({ type: 'none', ability: null });
        setTurnActions({ hasAttacked: false });
        await axios.post('http://localhost:8000/sessions/1/next_turn');
        // const res = ...; setSessionData(res.data); // <-- DELETE
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div style={{ color: 'red' }}>{error}</div>;
    if (!sessionData) return <div>No session data. Run seed script and refresh.</div>;

    return (
        <div className="game-room">
            <h1>Vyuha VTT</h1>
            <h2>{sessionData.campaign_name}</h2>

            {sessionData.current_mode === 'exploration' && (
                /* ... (No changes to JSX) ... */
                <div className="exploration-view">
                    {IS_GM && <button onClick={handlePrepareForCombat}>Prepare for Combat</button>}
                    <h3>Participants</h3>
                    <div className="participants-grid">{sessionData.participants.map((p) => (<CharacterCard key={p.id} participant={p} />))}</div>
                </div>
            )}

            {sessionData.current_mode === 'staging' && (
                <div className="staging-view">
                    <h3>Staging Phase: Place Heroes!</h3>
                    {IS_GM && <button onClick={handleBeginCombat}>Begin Combat!</button>}
                    <CombatGrid
                        participants={sessionData.participants}
                        onTokenMove={async (pId, x, y) => {
                            // This is an inline function, but the same logic applies.
                            // We make the request...
                            await axios.patch(`http://localhost:8000/sessions/1/`, { participant_positions: [{ participant_id: pId, x_pos: x, y_pos: y }]});
                            // ...and we no longer need to manually update state here.
                            // const res = ...; setSessionData(res.data); // <-- DELETE
                        }}
                        isGM={IS_GM}
                    />
                </div>
            )}

            {sessionData.current_mode === 'combat' && (
                /* ... (No changes to JSX) ... */
                <div className="combat-view">
                    <div className="combat-main-panel">
                        <h3>COMBAT! {selectedAction.type !== 'none' && `(SELECT A ${selectedAction.type === 'MOVE' ? 'SQUARE' : 'TARGET'})`}</h3>
                        <CombatGrid
                            participants={sessionData.participants}
                            activeParticipantId={activeParticipant?.id}
                            onGridClick={(x, y) => { if (selectedAction.type === 'MOVE' && isMyTurn) performAction({ actor_id: activeParticipant.id, action_type: 'MOVE', new_x: x, new_y: y })}}
                            onTokenClick={(targetId) => { if (selectedAction.type === 'TARGETING' && isMyTurn) performAction({ actor_id: activeParticipant.id, action_type: 'ATTACK', target_id: targetId, ability_id: selectedAction.ability.id })}}
                            isGM={false}
                            showMovementFor={selectedAction.type === 'MOVE' && isMyTurn ? activeParticipant : null}
                        />
                    </div>
                    <div className="combat-side-panel">
                        <InitiativeTracker participants={sessionData.participants} turnOrder={sessionData.turn_order} currentTurnIndex={sessionData.current_turn_index} />
                        <ActionPanel
                            abilities={activeCharacterAbilities}
                            onSelectMove={() => setSelectedAction({ type: 'MOVE' })}
                            onSelectAbility={(ability) => setSelectedAction({ type: 'TARGETING', ability })}
                            onEndTurn={handleEndTurn}
                            isMyTurn={isMyTurn}
                            selectedAction={selectedAction}
                            activeParticipant={activeParticipant}
                            turnActions={turnActions}
                        />
                        <GameLog messages={sessionData.log || []} />
                        {IS_GM && (
                            <div className="gm-controls-combat">
                              <button onClick={handleEndCombat}>End Combat</button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;