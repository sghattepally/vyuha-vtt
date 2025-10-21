import React, { useState } from 'react';
import { SKILL_CHECKS } from '../utils/gameData';

function SkillCheckModal({ participants, onClose, onSkillCheckRequested }) {
  const [targetIds, setTargetIds] = useState([]);
  const [checkType, setCheckType] = useState('dakshata');
  const [dc, setDc] = useState(10);
  const [description, setDescription] = useState('');

  const handleCheckboxChange = (id) => {
    setTargetIds((prev) =>
      prev.includes(id) ? prev.filter((pId) => pId !== id) : [...prev, id]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (targetIds.length === 0 || !description) {
      alert('Please select at least one target and provide a description.');
      return;
    }
    const payload = {
      participant_ids: targetIds,
      check_type: checkType,
      dc: parseInt(dc, 10),
      description,
    };
    onSkillCheckRequested(payload);
  };

  // Filter for participants who are actual players with characters
  const playerParticipants = participants.filter(p => p.character && p.player_id);

  return (
    <div className="modal-backdrop">
      <div className="modal skill-check-modal">
        <h2>Request Skill Check</h2>
        <form onSubmit={handleSubmit}>
          <div className="modal-content-split">
            {/* Left side for check details */}
            <div className="modal-left-panel">
              <div className="form-group">
                <label>Description</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g., To leap across the chasm"
                  required
                />
              </div>
              <div className="form-group">
                <label>Check Type</label>
                <select value={checkType} onChange={(e) => setCheckType(e.target.value)}>
                  <optgroup label="Attributes">
                    {SKILL_CHECKS.attributes.map(attr => (
                      <option key={attr.value} value={attr.value}>{attr.label}</option>
                    ))}
                  </optgroup>
                  <optgroup label="Derived Skills">
                    {SKILL_CHECKS.derived.map(skill => (
                      <option key={skill.value} value={skill.value}>{skill.label}</option>
                    ))}
                  </optgroup>
                </select>
              </div>
              <div className="form-group">
                <label>Difficulty Class (DC)</label>
                <input
                  type="number"
                  value={dc}
                  onChange={(e) => setDc(e.target.value)}
                  min="1"
                  required
                />
              </div>
            </div>
            {/* Right side for target selection */}
            <div className="modal-right-panel">
              <div className="form-group">
                <label>Targets ({targetIds.length})</label>
                <div className="checkbox-group scrollable">
                  {playerParticipants.map(p => (
                    <label key={p.id} className="checkbox-item">
                      <input
                        type="checkbox"
                        checked={targetIds.includes(p.id)}
                        onChange={() => handleCheckboxChange(p.id)}
                      />
                      {p.character.name}
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">Request Check</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default SkillCheckModal;