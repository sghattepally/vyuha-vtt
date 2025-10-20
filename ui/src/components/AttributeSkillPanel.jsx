import React from 'react';

const AttributeDisplay = ({ label, total, base, modifier, isPrimary }) => {
    // Determine the sign for the modifier display
    const sign = modifier >= 0 ? '+' : '-';
    
    // Class names for styling
    const labelClassName = isPrimary ? 'attribute-label primary-attribute' : 'attribute-label';

    return (
        <div className={`attribute-button ${isPrimary ? 'primary-attribute-button' : ''}`}>
            <span className={labelClassName}>{label}</span>
            <span className="attribute-total-large">{total}</span>
            <span className="attribute-breakdown-small">({base} {sign} {Math.abs(modifier)})</span>
        </div>
    );
};


function AttributeSkillPanel({ character, raceDetails, classDetails }) {
    // Safety check: Don't render if data is missing
    if (!character || !raceDetails || !classDetails) {
        return <div className="placeholder-text">Select a character to view details.</div>;
    }

    const finalAttributes = {
        bala: character.bala,
        dakshata: character.dakshata,
        dhriti: character.dhriti,
        buddhi: character.buddhi,
        prajna: character.prajna,
        samkalpa: character.samkalpa,
    };


    return (
        <div className="attribute-skill-panel-content">
            <div className="exploration-stats">
                <h3>{character.name}</h3>
                <div className='details-section'>
                    <h4>Lvl {character.level}</h4>
                    <h4>{raceDetails.name}</h4>
                    <h4>{classDetails.name}</h4>
                    <p>{classDetails.description}</p>
                </div>

                <div className="stat-block">
                    <p className="attributes-explanation">Total = Class Base + Race Bonus</p>
                    <div className="attributes-grid-buttons">
                        <AttributeDisplay label="Bala" total={finalAttributes.bala} base={classDetails.base_bala} modifier={raceDetails.bala_mod} isPrimary={classDetails.primary_attribute === 'Bala'} />
                        <AttributeDisplay label="Dakṣatā" total={finalAttributes.dakshata} base={classDetails.base_dakshata} modifier={raceDetails.dakshata_mod} isPrimary={classDetails.primary_attribute === 'Dakshata'} />
                        <AttributeDisplay label="Dhṛti" total={finalAttributes.dhriti} base={classDetails.base_dhriti} modifier={raceDetails.dhriti_mod} isPrimary={classDetails.primary_attribute === 'Dhriti'} />
                        <AttributeDisplay label="Buddhi" total={finalAttributes.buddhi} base={classDetails.base_buddhi} modifier={raceDetails.buddhi_mod} isPrimary={classDetails.primary_attribute === 'Buddhi'} />
                        <AttributeDisplay label="Prajñā" total={finalAttributes.prajna} base={classDetails.base_prajna} modifier={raceDetails.prajna_mod} isPrimary={classDetails.primary_attribute === 'Prajna'} />
                        <AttributeDisplay label="Saṃkalpa" total={finalAttributes.samkalpa} base={classDetails.base_samkalpa} modifier={raceDetails.samkalpa_mod} isPrimary={classDetails.primary_attribute === 'Samkalpa'} />
                    </div>
                </div>
            </div>
            {/* Future expansion: Add a section for character skills here */}
            <div className="skills-section">
                <h4>Skills</h4>
                <p>Skills list goes here.</p>
            </div>
        </div>
    );
}

export default AttributeSkillPanel;