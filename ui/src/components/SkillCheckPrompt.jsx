import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { getCheckResource } from '../utils/gameData'; // Helper from previous step

function SkillCheckPrompt({ sessionData, check, onAcknowledge, participant }) {
  const [useAdvantage, setUseAdvantage] = useState(false);
  const [isRolling, setIsRolling] = useState(false);
  const [result, setResult] = useState(null); // This will hold the roll result

  // This effect clears old results if a new check comes in
  useEffect(() => {
    setResult(null);
    setIsRolling(false);
  }, [check.id]);

  const handleRoll = async () => {
    setIsRolling(true);
    const payload = { skill_check_id: check.id, use_advantage: useAdvantage };
    try {
      // The backend now returns the result directly
      const response = await axios.post(`http://localhost:8000/sessions/${sessionData.id}/skill_check/roll`, payload);
      setResult(response.data); // We store that result in our state
    } catch (error) {
      console.error("Failed to perform skill check roll:", error);
      alert('Failed to roll. See console for details.');
      setIsRolling(false); // Re-enable button on error
    }
  };
  
  const advantageResource = getCheckResource(check.check_type);
  const hasResource = advantageResource === 'Tapas' 
      ? participant.current_tapas > 0 
      : participant.current_maya > 0;
    const disabledTitle = hasResource ? "" : `You have no ${advantageResource} points remaining.`;

  // The view for when the check is pending
  const renderPrompt = () => (
    <div className="skill-check-prompt-content">
      <p className="prompt-description">"{check.description}"</p>
      <div className="prompt-details">
        <span><strong>Check:</strong> {check.check_type.charAt(0).toUpperCase() + check.check_type.slice(1)}</span>
        <span><strong>DC:</strong> {check.dc}</span>
      </div>
      <div className="prompt-actions">
        <label title={disabledTitle} className={!hasResource ? 'disabled-label' : ''}>
              <input 
                type="checkbox" 
                checked={useAdvantage} 
                onChange={(e) => setUseAdvantage(e.target.checked)}
                disabled={!hasResource} 
              /> 
              Use {advantageResource} for Advantage?
          </label>
        <button onClick={handleRoll} disabled={isRolling} className="roll-button">{isRolling ? 'Rolling...' : 'Click to Roll'}</button>
      </div>
    </div>
  );

  // The view for after the roll is complete
  const renderResult = () => {
    const { success, total, roll, modifier, roll_breakdown, advantage_used } = result;
    const resultClass = success ? 'log-success' : 'log-failure';
    const advantageText = advantage_used ? ` (Advantage: ${roll_breakdown})` : '';

    return (
      <div className="skill-check-prompt-content">
        <div className="result-display">
          <div className={`result-total ${resultClass}`}>{total}</div>
          <div className="result-breakdown">
            <span>Roll: {roll}{advantageText}</span>
            <span>Modifier: {modifier >= 0 ? `+${modifier}` : modifier}</span>
          </div>
        </div>
        <div className={`result-outcome ${resultClass}`}>
          {success ? 'SUCCESS' : 'FAILURE'} (DC: {check.dc})
        </div>
        {/* The Close button now calls the onAcknowledge function */}
        <div className="prompt-actions">
          <button onClick={onAcknowledge} className="btn-secondary">Close</button>
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Conditionally render the prompt or the result based on our internal state */}
      {result ? renderResult() : renderPrompt()}
    </>
  );
}

export default SkillCheckPrompt;