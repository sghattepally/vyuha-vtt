import React from 'react';

function Panel({ title, children, onToggleCollapse }) {
  // We derive the collapsed state from the parent's layout state, not props
  return (
    <div className="panel">
      <div className="panel-header">
        <h3>{title}</h3>
        {onToggleCollapse && (
          <button onClick={onToggleCollapse}>
            {/* The character can be changed based on state if needed */}
            −
          </button>
        )}
      </div>
      <div className="panel-content">
        {children}
      </div>
    </div>
  );
}

export default Panel;