// ui/src/components/MovementOverlay.jsx
import React from 'react';

const GRID_SIZE = 50;

function MovementOverlay({ originX, originY, speed }) {
  if (originX === null || originY === null || speed <= 0) return null;

  const reachableSquares = [];
  // Simple Manhattan distance calculation
  for (let x = -speed; x <= speed; x++) {
    for (let y = -speed; y <= speed; y++) {
      if (Math.abs(x) + Math.abs(y) <= speed) {
        reachableSquares.push({ x: originX + x, y: originY + y });
      }
    }
  }

  return (
    <div className="movement-overlay">
      {reachableSquares.map((sq, i) => (
        <div 
          key={i} 
          className="movement-square" 
          style={{ left: sq.x * GRID_SIZE, top: sq.y * GRID_SIZE }}
        />
      ))}
    </div>
  );
}
export default MovementOverlay;