import React, { useState, useEffect } from 'react';
import axios from 'axios';

function EnvironmentalObjectPanel({ sessionId, isGM }) {
    const [objects, setObjects] = useState([]);
    const [selectedObject, setSelectedObject] = useState(null);
    
    useEffect(() => {
        fetchObjects();
    }, [sessionId]);
    
    const fetchObjects = async () => {
        try {
            const response = await axios.get(`http://localhost:8000/sessions/${sessionId}/environmental_objects`);
            setObjects(response.data);
        } catch (error) {
            console.error("Failed to fetch environmental objects:", error);
        }
    };
    
    const damageObject = async (objectId, damage, sectionId = null) => {
        try {
            await axios.patch(
                `http://localhost:8000/sessions/${sessionId}/environmental_objects/${objectId}/damage`,
                { damage, section_id: sectionId }
            );
        } catch (error) {
            console.error("Failed to damage object:", error);
        }
    };
    
    const repairObject = async (objectId, repairAmount, sectionId = null) => {
        try {
            await axios.patch(
                `http://localhost:8000/sessions/${sessionId}/environmental_objects/${objectId}/repair`,
                { repair_amount: repairAmount, section_id: sectionId }
            );
        } catch (error) {
            console.error("Failed to repair object:", error);
        }
    };
    
    if (objects.length === 0) {
        return (
            <div className="env-object-panel">
                <h4>Environmental Objects</h4>
                <p className="placeholder-text">No environmental objects in this session.</p>
                {isGM && (
                    <button className="btn-primary">+ Add Object</button>
                )}
            </div>
        );
    }
    
    return (
        <div className="env-object-panel">
            <h4>Environmental Objects</h4>
            
            {objects.map(obj => (
                <EnvironmentalObjectCard
                    key={obj.id}
                    object={obj}
                    isGM={isGM}
                    onDamage={(damage) => damageObject(obj.id, damage)}
                    onRepair={(repair) => repairObject(obj.id, repair)}
                    onSelect={() => setSelectedObject(obj)}
                />
            ))}
        </div>
    );
}

function EnvironmentalObjectCard({ object, isGM, onDamage, onRepair, onSelect }) {
    const integrityPercent = (object.current_integrity / object.max_integrity) * 100;
    const statusColor = integrityPercent > 60 ? 'green' : integrityPercent > 30 ? 'orange' : 'red';
    
    return (
        <div 
            className={`env-object-card ${!object.is_functional ? 'destroyed' : ''}`}
            onClick={onSelect}
        >
            <div className="env-object-header">
                <h5>{object.name}</h5>
                <span className="env-type-badge">{object.object_type}</span>
            </div>
            
            <div className="env-integrity-container">
                <div 
                    className={`env-integrity-bar integrity-${statusColor}`}
                    style={{ width: `${integrityPercent}%` }}
                />
                <span className="env-integrity-text">
                    {object.current_integrity} / {object.max_integrity}
                </span>
            </div>
            
            {!object.is_functional && (
                <div className="env-status-badge env-destroyed">
                    DESTROYED
                </div>
            )}
            
            {isGM && (
                <div className="env-quick-controls">
                    <button 
                        onClick={(e) => {
                            e.stopPropagation();
                            onDamage(5);
                        }}
                        className="btn-damage"
                    >
                        -5
                    </button>
                    <button 
                        onClick={(e) => {
                            e.stopPropagation();
                            onRepair(5);
                        }}
                        className="btn-repair"
                    >
                        +5
                    </button>
                </div>
            )}
        </div>
    );
}

export default EnvironmentalObjectPanel;