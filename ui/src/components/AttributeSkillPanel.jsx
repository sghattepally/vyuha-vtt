import React from 'react';
import { SKILL_CHECKS } from '../utils/gameData'; // For the skills list

// Helper function to calculate the modifier string (e.g., "+2", "-1")
const getModifier = (score) => {
    // Safety check to prevent NaN if score is not a number
    if (isNaN(score)) return 'N/A';
    const modifier = Math.floor((score - 10) / 2);
    return modifier >= 0 ? `+${modifier}` : `${modifier}`;
};

// --- Your original component, enhanced with the fixes ---
const AttributeDisplay = ({ label, total, base, raceMod, isPrimary }) => {
    const sign = raceMod >= 0 ? '+' : '-';
    const labelClassName = isPrimary ? 'attribute-label primary-attribute' : 'attribute-label';
    const breakdownText = `Base: ${base} | Race: ${sign}${Math.abs(raceMod)}`;

    return (
        <div 
            className={`attribute-button ${isPrimary ? 'primary-attribute-button' : ''}`}
            title={breakdownText} 
        >
            <span className={labelClassName}>{label}</span>
            <span className="attribute-total-large">{total}</span>
            <span className="attribute-breakdown-small">{getModifier(total)}</span>
        </div>
    );
};


const SkillDisplay = ({ skill, characterScores }) => {
    const mod1Value = parseInt(getModifier(characterScores[skill.attributes[0]]));
    const mod2Value = parseInt(getModifier(characterScores[skill.attributes[1]]));
    const skillModValue = Math.floor((mod1Value + mod2Value) / 2);
    const skillModifier = skillModValue >= 0 ? `+${skillModValue}` : `${skillModValue}`;

    return (
        <div className="skill-item" title={skill.description}> {/* HOVER: Shows skill description */}
            <span className="skill-label">{skill.label}</span>
            <span className="skill-modifier">{skillModifier}</span>
        </div>
    );
};

function AttributeSkillPanel({ character, raceDetails, classDetails }) {
    if (!character || !raceDetails || !classDetails) {
        return <div className="placeholder-text">Select a character to view details.</div>;
    }

    const finalAttributes = {
        bala: character.bala || 0, dakshata: character.dakshata || 0, dhriti: character.dhriti || 0,
        buddhi: character.buddhi || 0, prajna: character.prajna || 0, samkalpa: character.samkalpa || 0,
    };

    // Correctly structured data for easy mapping
    const attributeData = {
        deha: [
            { label: 'Bala',     key: 'bala' },
            { label: 'Dakṣatā',  key: 'dakshata' },
            { label: 'Dhṛti',    key: 'dhriti' },
        ],
        atman: [
            { label: 'Buddhi',   key: 'buddhi' },
            { label: 'Prajñā',   key: 'prajna' },
            { label: 'Saṃkalpa', key: 'samkalpa' },
        ]
    };

    return (
        <div className="attribute-skill-panel-content">
            <div className="exploration-stats">
                <h3>{character.name}</h3>
                <div className='details-section'>
                    <h4>Lvl {character.level}</h4>
                    <h4>{raceDetails.name} {classDetails.name}</h4>
                </div>
                <div className="attributes-grid-vertical">
                    {Object.entries(attributeData).map(([groupName, attrs]) => (
                        <div className="attribute-column" key={groupName}>
                            <h5>{groupName} ({groupName === 'deha' ? 'Body' : 'Spirit'})</h5>
                            {attrs.map(attr => (
                                <AttributeDisplay 
                                key={attr.key}
                                    label={attr.label}
                                    total={finalAttributes[attr.key]}
                                    base={classDetails[`base_${attr.key}`]}
                                    raceMod={raceDetails[`${attr.key}_mod`]}
                                    isPrimary={classDetails.primary_attribute.toLowerCase() === attr.key}
                                />
                            ))}
                        </div>
                    ))}
                </div>
            </div>
            <div className="skills-section">
                <h4>Skills</h4>
                <div className="skills-list">
                    {SKILL_CHECKS.derived.map(skill => (
                        <SkillDisplay key={skill.value} skill={skill} characterScores={finalAttributes} />
                    ))}
                </div>
            </div>
        </div>
    );
}

export default AttributeSkillPanel;