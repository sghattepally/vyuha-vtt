import React from 'react';

function Panel({ title, children, onCollapse, isCollapsed, contentClassName, tabs, activeTab, onTabClick }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="header-main-content">
          <h3>{title}</h3>
          {/* If tabs are provided, render them */}
          {tabs && (
            <div className="panel-header-tabs">
              {tabs.map(tab => (
                <button
                  key={tab.key}
                  className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => onTabClick(tab.key)}
                  disabled={tab.disabled}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          )}
        </div>
        {onCollapse && (
          <button className="panel-collapse-button" onClick={onCollapse}>
            {isCollapsed ? '＋' : '−'}
          </button>
        )}
      </div>
      {!isCollapsed && (
        <div className={`panel-content ${contentClassName || ''}`}>
          {children}
        </div>
      )}
    </div>
  );
}

export default Panel;