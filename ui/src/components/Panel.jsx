// ui/src/components/Panel.jsx

import React from 'react';

function Panel({ title, children, isCollapsed, onToggleCollapse }) {
  return (
    <div className={`panel ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="panel-header">
        <h3>{title}</h3>
        <button onClick={onToggleCollapse}>
          {isCollapsed ? '+' : '−'}
        </button>
      </div>
      {!isCollapsed && (
        <div className="panel-content">
          {children}
        </div>
      )}
    </div>
  );
}

export default Panel;