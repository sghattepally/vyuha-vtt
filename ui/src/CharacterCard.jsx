// ui/src/CharacterCard.jsx

import React from 'react';

// A helper function to calculate the Vyuha attribute modifier
const getModifier = (score) => {
  const modifier = Math.floor((score - 10) / 2);
  // Return it as a string with a + or - sign
  return modifier >= 0 ? `+${modifier}` : `${modifier}`;
};

function CharacterCard({ character }) {
  // We receive the full character data as a "prop"
  return (
    <div className="character-card">
      <h4>{character.character_name}</h4>
      <p><strong>Prāṇa:</strong> {character.current_prana}</p>
      <div className="attributes">
        <p><strong>Bala:</strong> {character.template.bala} ({getModifier(character.template.bala)})</p>
        <p><strong>Dakṣatā:</strong> {character.template.dakshata} ({getModifier(character.template.dakshata)})</p>
        {/* ... you would do this for all six attributes ... */}
      </div>
    </div>
  );
}

export default CharacterCard;