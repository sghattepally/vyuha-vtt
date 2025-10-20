import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * A sub-component to display a single attribute with its detailed breakdown.
 */
const AttributeDisplay = ({ label, total, base, modifier, isPrimary }) => {
    const sign = modifier >= 0 ? '+' : '-';
    const labelClassName = isPrimary ? 'attribute-label primary-attribute' : 'attribute-label';

    return (
        <div className={`attribute-button ${isPrimary ? 'primary-attribute-button' : ''}`}>
            <span className={labelClassName}>{label}</span>
            <span className="attribute-total-large">{total}</span>
            <span className="attribute-breakdown-small">({base} {sign} {Math.abs(modifier)})</span>
        </div>
    );
};

/**
 * A modal component for creating new player characters or NPC templates.
 */
function CharacterCreator({ ownerId, onCharacterCreated, onClose }) {
    // Form state
    const [name, setName] = useState('');
    const [selectedRace, setSelectedRace] = useState('');
    const [selectedClass, setSelectedClass] = useState('');

    // Data state from API
    const [races, setRaces] = useState([]);
    const [classes, setClasses] = useState([]);
    
    // UI/Error state
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);

    // Fetch available races and classes when the component mounts
    useEffect(() => {
        const fetchRules = async () => {
            try {
                setLoading(true);
                const [racesRes, classesRes] = await Promise.all([
                    axios.get('http://localhost:8000/rules/races'),
                    axios.get('http://localhost:8000/rules/classes')
                ]);
                setRaces(racesRes.data);
                setClasses(classesRes.data);
            } catch (err) {
                setError("Failed to load character creation data.");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchRules();
    }, []);

    // Handle form submission
    const handleSubmit = async (e) => {
        e.preventDefault();
    setError('');
    if (!ownerId) {
        setError("Cannot create character: Player data is not yet available. Please close the modal and try again.");
        console.error("Submission blocked: ownerId is missing.");
        return; // Stop the function completely if there's no owner.
    }
        if (!name || !selectedRace || !selectedClass) {
            alert("Please fill out all fields.");
            return;
        }
        try {
            const payload = {
                name,
                race: selectedRace,
                char_class: selectedClass,
                owner_id: ownerId,
            };
            await axios.post('http://localhost:8000/characters/', payload);
            onCharacterCreated();
            onClose();
        } catch (err) {
    // Check if the detailed error from FastAPI exists and is an array
    if (err.response?.data?.detail && Array.isArray(err.response.data.detail)) {
        // Extract the message from the first error object in the array
        const errorMessage = err.response.data.detail[0].msg;
        setError(errorMessage);
    } else {
        // Fallback for other types of errors
        setError('An unknown error occurred. Please check the console.');
    }
}
    };

    const raceDetails = races.find(r => r.name === selectedRace);
    const classDetails = classes.find(c => c.name === selectedClass);
    
    const finalAttributes = raceDetails && classDetails ? {
        bala: classDetails.base_bala + raceDetails.bala_mod,
        dakshata: classDetails.base_dakshata + raceDetails.dakshata_mod,
        dhriti: classDetails.base_dhriti + raceDetails.dhriti_mod,
        buddhi: classDetails.base_buddhi + raceDetails.buddhi_mod,
        prajna: classDetails.base_prajna + raceDetails.prajna_mod,
        samkalpa: classDetails.base_samkalpa + raceDetails.samkalpa_mod,
    } : null;

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content creator-modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-scrollable-content">
                    <h2>Create a New Hero</h2>
                    <form onSubmit={handleSubmit} id="character-creator-form" className="character-creator-form">
                        {loading ? (
                            <p>Loading rules...</p>
                        ) : (
                            <div className="character-creator-layout">
                                <div className="character-creator-left-panel">
                                    <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Character Name" required />
                                    <label>Race</label>
                                    <select value={selectedRace} onChange={(e) => setSelectedRace(e.target.value)} required>
                                        <option value="" disabled>-- Select a Race --</option>
                                        {races.map(race => <option key={race.name} value={race.name}>{race.name}</option>)}
                                    </select>
                                    {raceDetails && <div className="description-tooltip"><p>{raceDetails.description}</p></div>}

                                    <label>Class</label>
                                    <select value={selectedClass} onChange={(e) => setSelectedClass(e.target.value)} required>
                                        <option value="" disabled>-- Select a Class --</option>
                                        {classes.map(cls => <option key={cls.name} value={cls.name}>{cls.name}</option>)}
                                    </select>
                                    {classDetails && <div className="description-tooltip"><p>{classDetails.description}</p></div>}
                                </div>

                                <div className="character-creator-right-panel">
                                    <h4>Final Attributes</h4>
                                    {/* NEW: Explanation paragraph added below the header */}
                                    <p className="attributes-explanation">Total = Class Base + Race Bonus</p>
                                    
                                    {finalAttributes && classDetails && raceDetails ? (
                                        <div className="attributes-grid-buttons">
                                            <AttributeDisplay label="Bala" total={finalAttributes.bala} base={classDetails.base_bala} modifier={raceDetails.bala_mod} isPrimary={classDetails.primary_attribute === 'Bala'} />
                                            <AttributeDisplay label="Dakṣatā" total={finalAttributes.dakshata} base={classDetails.base_dakshata} modifier={raceDetails.dakshata_mod} isPrimary={classDetails.primary_attribute === 'Dakshata'} />
                                            <AttributeDisplay label="Dhṛti" total={finalAttributes.dhriti} base={classDetails.base_dhriti} modifier={raceDetails.dhriti_mod} isPrimary={classDetails.primary_attribute === 'Dhriti'} />
                                            <AttributeDisplay label="Buddhi" total={finalAttributes.buddhi} base={classDetails.base_buddhi} modifier={raceDetails.buddhi_mod} isPrimary={classDetails.primary_attribute === 'Buddhi'} />
                                            <AttributeDisplay label="Prajñā" total={finalAttributes.prajna} base={classDetails.base_prajna} modifier={raceDetails.prajna_mod} isPrimary={classDetails.primary_attribute === 'Prajna'} />
                                            <AttributeDisplay label="Saṃkalpa" total={finalAttributes.samkalpa} base={classDetails.base_samkalpa} modifier={raceDetails.samkalpa_mod} isPrimary={classDetails.primary_attribute === 'Samkalpa'} />
                                        </div>
                                    ) : (
                                        <p className="selection-prompt">Select a Race and Class to see attributes.</p>
                                    )}
                                </div>
                            </div>
                        )}
                    </form>
                </div>
                <div className="modal-actions">
                    <button type="button" onClick={onClose}>Cancel</button>
                    <button type="submit" form="character-creator-form" disabled={loading || !selectedRace || !selectedClass}>Create</button>
                </div>
                {error && <p className="error-message">{error}</p>}
            </div>
        </div>
    );
}

export default CharacterCreator;