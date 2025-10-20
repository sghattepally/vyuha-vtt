import React from 'react';

// Helper to format the modifier string (e.g., +2, -1)
const formatModifier = (score) => {
    const mod = Math.floor((score - 10) / 2);
    return mod >= 0 ? `+${mod}` : mod;
};

// Map attribute keys to their display names
const ATTRIBUTE_NAMES = {
    'bala': 'Bala', 'dakshata': 'Dakṣatā', 'dhriti': 'Dhṛti',
    'buddhi': 'Buddhi', 'prajna': 'Prajñā', 'samkalpa': 'Saṃkalpa'
};

function ActionPanel({ sessionData, activeCharacterId }) {
    if (!sessionData || !activeCharacterId) {
        return <div className="action-panel-placeholder">Select a character</div>;
    }

    const activeParticipant = sessionData.participants.find(p => p.id === activeCharacterId);
    if (!activeParticipant) {
        return <div className="action-panel-placeholder">Character not found in session</div>;
    }

    const character = activeParticipant.character;

    // --- RENDER LOGIC ---
    if (sessionData.mode === 'COMBAT') {
        // --- COMBAT MODE ---
        return (
            <div className="action-panel-content">
                <h3>{character.name}'s Actions</h3>
                <div className="ability-list">
                    <p>Combat actions will be displayed here.</p>
                    {/* Example of how you might list abilities in the future */}
                    {/* {character.abilities.map(ability => <button key={ability.id}>{ability.name}</button>)} */}
                </div>
            </div>
        );
    } else {
        // --- EXPLORATION MODE ---
        const { race, char_class } = character;

        return (
            <div className="action-panel-content exploration-stats">
                <h3>{character.name}</h3>
                <div className='details-section'>
                    <h4>{race.name} {char_class.name}</h4>
                    <p>{char_class.description}</p>
                </div>

                <div className='stat-block'>
                    <div className='stat-row header'>
                        <span>Attribute</span>
                        <span>Total</span>
                        <span>Mod</span>
                        <span>Base</span>
                        <span>Race</span>
                    </div>
                    {Object.entries(ATTRIBUTE_NAMES).map(([key, name]) => {
                        const baseScore = char_class[`base_${key}`];
                        const raceMod = race[`${key}_mod`];
                        const totalScore = character[key]; // Use the final calculated score

                        return (
                            <div className='stat-row' key={key}>
                                <span>{name}</span>
                                <span>{totalScore}</span>
                                <span>{formatModifier(totalScore)}</span>
                                <span>{baseScore}</span>
                                <span className={raceMod >= 0 ? 'positive' : 'negative'}>
                                    {raceMod > 0 ? `+${raceMod}` : raceMod}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    }
}

export default ActionPanel;