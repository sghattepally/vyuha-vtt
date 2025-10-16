// ui/src/components/CharacterCard.jsx
import React from 'react';

const getModifier = (score) => {
  const modifier = Math.floor((score - 10) / 2);
  return modifier >= 0 ? `+${modifier}` : `${modifier}`;
};

function CharacterCard({ participant }) {
  const characterTemplate = participant.character;

  return (
    <div className="character-card">
      <h4>{characterTemplate.name}</h4>
      <p><strong>Prāṇa:</strong> {participant.current_prana} / {characterTemplate.max_prana}</p>
      <div className="attributes">
        <p><strong>Bala:</strong> {characterTemplate.bala} ({getModifier(characterTemplate.bala)})</p>
        <p><strong>Dakṣatā:</strong> {characterTemplate.dakshata} ({getModifier(characterTemplate.dakshata)})</p>
        <p><strong>Dhṛti:</strong> {characterTemplate.dhriti} ({getModifier(characterTemplate.dhriti)})</p>
        <p><strong>Buddhi:</strong> {characterTemplate.buddhi} ({getModifier(characterTemplate.buddhi)})</p>
        <p><strong>Prajñā:</strong> {characterTemplate.prajna} ({getModifier(characterTemplate.prajna)})</p>
        <p><strong>Saṃkalpa:</strong> {characterTemplate.samkalpa} ({getModifier(characterTemplate.samkalpa)})</p>
      </div>
    </div>
  );
}

export default CharacterCard;