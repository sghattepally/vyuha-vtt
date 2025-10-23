import React, { useState } from 'react';
import AttributeSkillPanel from './AttributeSkillPanel';

function CharacterSheet({ character }) {
  if (!character) {
    return <div className="placeholder-text">Character details will appear here.</div>;
  }

  return (
    <div className="character-sheet">
      <div className="sheet-content">
          <AttributeSkillPanel character={character} />
      
      </div>
    </div>
  );
}

export default CharacterSheet;