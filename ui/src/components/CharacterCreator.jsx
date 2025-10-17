// ui/src/components/CharacterCreator.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';

function CharacterCreator({ ownerId, onCharacterCreated, onClose }) {
  const [name, setName] = useState('');
  const [selectedRace, setSelectedRace] = useState('');
  const [selectedClass, setSelectedClass] = useState('');
  
  const [races, setRaces] = useState([]);
  const [classes, setClasses] = useState([]);
  const [error, setError] = useState('');

  // Fetch available races and classes when the component loads
  useEffect(() => {
    axios.get('http://localhost:8000/rules/races').then(res => {
      setRaces(res.data);
      setSelectedRace(res.data[0] || ''); // Default to the first race
    });
    axios.get('http://localhost:8000/rules/classes').then(res => {
      setClasses(res.data);
      setSelectedClass(res.data[0] || ''); // Default to the first class
    });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const payload = {
        name,
        race: selectedRace,
        character_class: selectedClass,
        owner_id: ownerId
      };
      await axios.post('http://localhost:8000/characters/', payload);
      onCharacterCreated(); // Tell the lobby to refresh its character list
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create character.');
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h2>Create a New Hero</h2>
        <form onSubmit={handleSubmit} className="character-creator-form">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Character Name"
            required
          />
          <label>Race</label>
          <select value={selectedRace} onChange={(e) => setSelectedRace(e.target.value)}>
            {races.map(race => <option key={race} value={race}>{race}</option>)}
          </select>
          <label>Class</label>
          <select value={selectedClass} onChange={(e) => setSelectedClass(e.target.value)}>
            {classes.map(cls => <option key={cls} value={cls}>{cls}</option>)}
          </select>
          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button type="submit">Create</button>
          </div>
          {error && <p className="error-message">{error}</p>}
        </form>
      </div>
    </div>
  );
}

export default CharacterCreator;