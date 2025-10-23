import React, { useState, useEffect } from 'react';
import axios from 'axios';
import InventoryMenu from './InventoryMenu.jsx';
import GiveItemPlayerModal from './GiveItemPlayerModal.jsx';

const ItemTile = ({ invItem, onClick }) => {
  const { item, quantity, is_equipped } = invItem;
  const tooltipText = `${item.puranic_name}\n${item.english_name} (${item.item_type})\n${item.description}`;
  const placeholderLetter = item.puranic_name.charAt(0).toUpperCase();
  const tileClassName = `item-tile ${is_equipped ? 'equipped-tile' : ''}`;

  return (
    <div className={tileClassName} title={tooltipText} onClick={onClick}>
      <div className="item-placeholder">{placeholderLetter}</div>
      <div className="item-tile-name">{item.puranic_name}</div>
      {item.is_stackable && quantity > 1 && (
        <div className="item-quantity-badge">{quantity}</div>
      )}
    </div>
  );
};

function InventoryPanel({ character, participants }) {
  const [inventory, setInventory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [giveModalData, setGiveModalData] = useState({ isOpen: false, item: null });
  const [menuData, setMenuData] = useState({ visible: false, position: { x: 0, y: 0 }, selectedItem: null });

  // This useEffect now correctly uses the full URL
  useEffect(() => {
    if (character?.id) {
      setIsLoading(true);
      axios.get(`http://localhost:8000/character/${character.id}/inventory`)
        .then(response => setInventory(response.data))
        .catch(error => console.error("Failed to fetch inventory:", error))
        .finally(() => setIsLoading(false));
    }
  }, [character?.id]);

  // This syncs the inventory with the main sessionData from websockets
  useEffect(() => {
    if (character?.inventory) {
      setInventory(character.inventory);
    }
  }, [character?.inventory]);

  const handleItemClick = (event, invItem) => {
    event.preventDefault();
    setMenuData({
      visible: true,
      position: { x: event.pageX, y: event.pageY },
      selectedItem: invItem,
    });
  };

  const closeMenu = () => setMenuData({ ...menuData, visible: false });

  // --- API HANDLERS WITH CORRECTED URLS ---

  const handleToggleEquip = (inventoryId) => {
    axios.post(`http://localhost:8000/character/${character.id}/inventory/${inventoryId}/toggle-equip`)
      .catch(err => console.error("Failed to toggle equip state:", err));
  };

  const handleUseItem = (inventoryId) => {
    axios.post(`http://localhost:8000/inventory/${inventoryId}/use`)
      .catch(err => console.error("Failed to use item:", err));
  };

  const handleDestroyItem = (inventoryId, itemName) => {
    if (window.confirm(`Are you sure you want to destroy ${itemName}?`)) {
      axios.delete(`http://localhost:8000/inventory/${inventoryId}/destroy`)
        .catch(err => console.error("Failed to destroy item:", err));
    }
  };

  const handleGiveItem = (targetCharacterId, quantity) => {
    if (!giveModalData.item) return;
    const payload = { target_character_id: targetCharacterId, quantity: quantity || 1 };
    axios.post(`http://localhost:8000/inventory/${giveModalData.item.id}/give`, payload)
      .catch(err => console.error("Failed to give item:", err))
      .finally(() => setGiveModalData({ isOpen: false, item: null }));
  };

  const getMenuOptions = () => {
    if (!menuData.selectedItem) return [];
    const item = menuData.selectedItem.item;
    const invId = menuData.selectedItem.id;
    const options = [];

    if (menuData.selectedItem.is_equipped) {
      options.push({ label: 'Unequip', action: () => handleToggleEquip(invId) });
    } else {
      if (item.item_type === 'weapon' || item.item_type === 'armor') {
        options.push({ label: 'Equip', action: () => handleToggleEquip(invId) });
      }
    }
    if (item.item_type === 'potion') {
      options.push({ label: 'Consume', action: () => handleUseItem(invId) });
    }
    
    const otherParticipants = participants.filter(p => p.character && p.character.id !== character.id);
    if (otherParticipants.length > 0) {
      options.push({ 
        label: 'Give to...', 
        action: () => setGiveModalData({ isOpen: true, item: menuData.selectedItem })
      });
    }

    options.push({ label: 'Destroy', action: () => handleDestroyItem(invId, item.puranic_name), isDestructive: true });
    return options;
  };

  if (isLoading) {
    return <div className="placeholder-text">Loading inventory...</div>;
  }
  
  const equippedItems = inventory.filter(item => item.is_equipped);
  const unequippedItems = inventory.filter(item => !item.is_equipped);
  const otherParticipants = participants.filter(p => p.character && p.character.id !== character.id);

  return (
    <div className="inventory-panel-grid" onContextMenu={(e) => e.preventDefault()}>
      <div className="inventory-currency">Gold: {character.currency || 0}</div>
      
      <div className="inventory-section">
        <h5 className="inventory-section-header">Equipped</h5>
        <div className="item-grid">
          {equippedItems.map(invItem => 
            <ItemTile key={invItem.id} invItem={invItem} onClick={(e) => handleItemClick(e, invItem)} />
          )}
        </div>
      </div>
      
      <div className="inventory-section">
        <h5 className="inventory-section-header">Inventory</h5>
        <div className="item-grid scrollable">
          {unequippedItems.map(invItem => 
            <ItemTile key={invItem.id} invItem={invItem} onClick={(e) => handleItemClick(e, invItem)} />
          )}
        </div>
      </div>

      {giveModalData.isOpen && (
        <GiveItemPlayerModal
          currentCharacter={character}
          otherParticipants={otherParticipants}
          invItem={giveModalData.item}
          onGive={handleGiveItem}
          onClose={() => setGiveModalData({ isOpen: false, item: null })}
        />
      )}
      {menuData.visible && (
        <InventoryMenu
          options={getMenuOptions()}
          position={menuData.position}
          onClose={closeMenu}
        />
      )}
    </div>
  );
}

export default InventoryPanel;