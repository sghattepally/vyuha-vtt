import React from 'react';

function ResourceDots({ current, max, color, resourceName }) {
  // Create an array of dots to render
  const dots = [];
  for (let i = 1; i <= max; i++) {
    const isFilled = i <= current;
    dots.push(
      <div
        key={i}
        className={`resource-dot ${isFilled ? 'filled' : ''}`}
        style={isFilled ? { backgroundColor: color, boxShadow: `0 0 8px ${color}` } : {}}
      ></div>
    );
  }

  return (
    <div className="resource-dots-container" title={`${resourceName}: ${current} / ${max}`}>
      {dots}
    </div>
  );
}

export default ResourceDots;