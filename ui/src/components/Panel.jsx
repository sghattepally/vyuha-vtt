import React from 'react';

function Panel({ title, children, onCollapse, isCollapsed, contentClassName }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h3>{title}</h3>
        {/*
          This now checks for the onCollapse function.
          The button's text will change based on the isCollapsed prop.
        */}
        {onCollapse && (
          <button className="panel-collapse-button" onClick={onCollapse}>
            {isCollapsed ? '＋' : '−'}
          </button>
        )}
      </div>
      {/*
        The content is now conditionally rendered so it doesn't take up
        space in the DOM when the panel is collapsed.
      */}
      {!isCollapsed && (
        <div className={`panel-content ${contentClassName}`}>
          {children}
        </div>
      )}
    </div>
  );
}

export default Panel;