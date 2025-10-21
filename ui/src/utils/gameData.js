export const SKILL_CHECKS = {
  attributes: [
    { value: 'bala', label: 'Bala (Strength)' },
    { value: 'dakshata', label: 'Dakṣatā (Agility)' },
    { value: 'dhriti', label: 'Dhṛti (Endurance)' },
    { value: 'buddhi', label: 'Buddhi (Intellect)' },
    { value: 'prajna', label: 'Prajñā (Awareness)' },
    { value: 'samkalpa', label: 'Saṃkalpa (Willpower)' },
  ],
  derived: [
    { value: 'moha',       label: 'Moha (Charm)',       attributes: ['prajna', 'samkalpa'], description: 'Influence or deceive others through personality and persuasion.' },
    { value: 'bhaya',      label: 'Bhaya (Intimidation)', attributes: ['bala', 'samkalpa'],   description: 'Coerce or frighten others through sheer presence or threats.' },
    { value: 'chhalana',   label: 'Chhalana (Stealth)',   attributes: ['dakshata', 'buddhi'],   description: 'Move silently, remain unseen, and act without being noticed.' },
    { value: 'anveshana',  label: 'Anveshana (Investigate)', attributes: ['buddhi', 'prajna'],   description: 'Deduce information, uncover clues, and analyze details.' },
    { value: 'sahanashakti', label: 'Sahanashakti (Resilience)', attributes: ['dhriti', 'samkalpa'], description: 'Endure hardship and resist physical or mental pain.' },
    { value: 'yukti',      label: 'Yukti (Tactics)',      attributes: ['dakshata', 'prajna'],   description: 'Assess a situation and formulate a plan for strategic advantage.' },
    { value: 'prerana',    label: 'Prerana (Inspiration)', attributes: ['prajna', 'samkalpa'],   description: 'Captivate an audience, inspire allies, or convey a message.' },
    { value: 'atindriya',  label: 'Atindriya (Perception)', attributes: ['bala', 'prajna'],      description: 'Notice hidden details and spot impending danger.' },
  ],
};

export const ATTRIBUTE_TO_RESOURCE = {
    bala: "Tapas", dakshata: "Tapas", dhriti: "Tapas",
    buddhi: "Māyā", prajna: "Māyā", samkalpa: "Māyā",
};

export const getCheckResource = (checkType) => {
    const derived = SKILL_CHECKS.derived.find(d => d.value === checkType);
    // For derived skills, the resource is tied to the second (spiritual) attribute
    const primaryAttribute = derived ? derived.attributes[1] : checkType;
    return ATTRIBUTE_TO_RESOURCE[primaryAttribute] || "Tapas";
};