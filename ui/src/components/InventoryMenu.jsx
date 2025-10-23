import React, { useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';

function InventoryMenu({ options, position, onClose }) {
  const menuRef = useRef(null);

  // This effect handles clicking outside the menu to close it
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose();
      }
    };
    // Add the event listener when the menu is open
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  if (!position) return null;

  return ReactDOM.createPortal(
    <div
      ref={menuRef}
      className="inventory-menu"
      style={{ top: `${position.y}px`, left: `${position.x}px` }}
    >
      <ul>
        {options.map(option => (
          <li
            key={option.label}
            onClick={() => {
              option.action(); // Execute the action
              onClose();       // Close the menu
            }}
            className={option.isDestructive ? 'destructive' : ''}
          >
            {option.label}
          </li>
        ))}
      </ul>
    </div>,
    document.getElementById('menu-root')
  );
}

export default InventoryMenu;