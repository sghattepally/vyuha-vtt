// ui/src/components/CombatGrid.jsx

import React, { useRef } from 'react';
import Draggable from 'react-draggable';
import Token from './Token';
import MovementOverlay from './MovementOverlay';

const GRID_SIZE = 50;

function CombatGrid({ participants, onTokenMove, isGM, activeParticipantId, onGridClick, onTokenClick, showMovementFor }) {
    const gridRef = useRef(null);

    const handleGridSquareClick = (e) => {
        if (e.target === gridRef.current && onGridClick) {
            const rect = e.currentTarget.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / GRID_SIZE);
            const y = Math.floor((e.clientY - rect.top) / GRID_SIZE);
            onGridClick(x, y);
        }
    };

    const gridTokens = participants.filter(p => p.x_pos !== null && p.y_pos !== null);
    const shelfTokens = participants.filter(p => p.x_pos === null || p.y_pos === null);

    const handleStop = (e, data, participantId, isFromShelf = false) => {
        if (!onTokenMove || !isGM) return;
        let newX, newY;
        if (isFromShelf) {
            const gridRect = gridRef.current.getBoundingClientRect();
            newX = Math.floor((e.clientX - gridRect.left) / GRID_SIZE);
            newY = Math.floor((e.clientY - gridRect.top) / GRID_SIZE);
        } else {
            newX = Math.round(data.x / GRID_SIZE);
            newY = Math.round(data.y / GRID_SIZE);
        }
        onTokenMove(participantId, newX, newY);
    };

    return (
        <>
            {shelfTokens.length > 0 && isGM && (
                <div className="token-shelf">
                    {shelfTokens.map(p => {
                        // --- FIX PART 1: nodeRef is now applied to SHELF tokens ---
                        const nodeRef = useRef(null);
                        return (
                            <Draggable key={p.id} nodeRef={nodeRef} onStop={(e, data) => handleStop(e, data, p.id, true)} disabled={!isGM}>
                                <div ref={nodeRef} className="token-on-shelf">
                                    <Token participant={p} isActive={p.id === activeParticipantId} onTokenClick={onTokenClick} />
                                </div>
                            </Draggable>
                        );
                        // --- END OF FIX ---
                    })}
                </div>
            )}

            <div ref={gridRef} className="grid-container" onClick={handleGridSquareClick}>
                {showMovementFor && <MovementOverlay originX={showMovementFor.x_pos} originY={showMovementFor.y_pos} speed={showMovementFor.remaining_speed} />}
                
                {gridTokens.map((p) => {
                    // --- FIX PART 2: nodeRef is correctly applied to GRID tokens ---
                    const nodeRef = useRef(null);
                    return (
                        <Draggable 
                            key={p.id} 
                            nodeRef={nodeRef}
                            bounds="parent" 
                            grid={[GRID_SIZE, GRID_SIZE]} 
                            position={{ x: p.x_pos * GRID_SIZE, y: p.y_pos * GRID_SIZE }} 
                            onStop={(e, data) => handleStop(e, data, p.id)} 
                            disabled={!onTokenMove || !isGM}
                        >
                            <div ref={nodeRef} style={{ width: 0, height: 0 }}>
                                <Token participant={p} isActive={p.id === activeParticipantId} onTokenClick={onTokenClick} />
                            </div>
                        </Draggable>
                    );
                    // --- END OF FIX ---
                })}
            </div>
        </>
    );
}

export default CombatGrid;