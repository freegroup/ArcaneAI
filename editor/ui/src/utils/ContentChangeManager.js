import store from '@/store';

/**
 * ContentChangeManager
 * 
 * Central handler for content changes across game and encounter files.
 * Keeps all files consistent when states, connections, or other content changes.
 * 
 * All handler methods receive:
 * @param {string} emitter - The emitter of the change: 'game' | encounterName
 * @param {object} data - The persistence data (JSON from getPersistenceData())
 */
class ContentChangeManager {
  /**
   * Handle when a state's properties change (name, position, etc.)
   * Updates the state in both world (game) and all encounters.
   * @param {string} emitter - 'game' | encounterName
   * @param {object} data - State persistence data
   */
  static handleStateChange(emitter, data) {
    console.log(`[ContentChangeManager] State changed in ${emitter}:`, data.id, data);
    
    if (!data || !data.id) {
      console.warn('[ContentChangeManager] No valid state data provided');
      return;
    }

    // Step 1: Create copy of state data without position-specific properties
    const stateData = { ...data };
    delete stateData.x;
    delete stateData.y;
    
    console.log('[ContentChangeManager] Syncing stateData:', stateData);

    // Inline helper to update state in a diagram
    const _updateState = (diagram) => {
      if (!Array.isArray(diagram)) return false;
      const state = diagram.find(item => item.type === data.type && item.id === data.id);
      if (state) {
        Object.assign(state, stateData);
        return true;
      }
      return false;
    };

    // Step 2: Update state in World (gameDiagram)
    const gameDiagram = store.state.game.gameDiagram;
    if (_updateState(gameDiagram)) {
      console.log('[ContentChangeManager] Updated state in World');
    }

    // Step 3: Update state in ALL encounters
    const encounters = store.state.encounters.encounters;
    for (const [encounterName, encounterData] of Object.entries(encounters)) {
      if (encounterData && encounterData.diagram) {
        if (_updateState(encounterData.diagram)) {
          console.log(`[ContentChangeManager] Updated state in encounter: ${encounterName}`);
        }
      }
    }
  }

  /**
   * Handle when a state trigger's properties change (name, conditions, actions, etc.)
   * @param {string} emitter - 'game' | encounterName
   * @param {object} data - StateTrigger persistence data
   */
  static handleStateTriggerChange(emitter, data) {
    console.log(`[ContentChangeManager] StateTrigger changed in ${emitter}:`, data.id, data);
  }

  /**
   * Handle when a connection's properties change (name, userData, etc.)
   * Connections (TriggerConnection) have `vertex` arrays for routing which are position-specific.
   * @param {string} emitter - 'game' | encounterName
   * @param {object} data - Connection persistence data
   */
  static handleConnectionChange(emitter, data) {
    console.log(`[ContentChangeManager] Connection changed in ${emitter}:`, data.id, data);
    
    if (!data || !data.id) {
      console.warn('[ContentChangeManager] No valid connection data provided');
      return;
    }

    // Create copy of connection data without position-specific properties
    const connectionData = { ...data };
    delete connectionData.vertex;  // Routing vertices are position-specific per diagram
    delete connectionData.routingMetaData;  // Also position-specific
    
    console.log('[ContentChangeManager] Syncing connectionData:', connectionData);

    // Helper to find and update connection in diagram
    const _updateConnection = (diagram) => {
      if (!Array.isArray(diagram)) return false;
      const connection = diagram.find(item => item.type === 'TriggerConnection' && item.id === data.id);
      if (connection) {
        // Update name and userData but preserve vertex/routing
        if (connectionData.name !== undefined) connection.name = connectionData.name;
        if (connectionData.userData !== undefined) {
          connection.userData = { ...connection.userData, ...connectionData.userData };
        }
        if (connectionData.dasharray !== undefined) connection.dasharray = connectionData.dasharray;
        return true;
      }
      return false;
    };

    // Update connection in World (gameDiagram)
    const gameDiagram = store.state.game.gameDiagram;
    if (_updateConnection(gameDiagram)) {
      console.log('[ContentChangeManager] Updated connection in World');
    }

    // Update connection in ALL encounters
    const encounters = store.state.encounters.encounters;
    for (const [encounterName, encounterData] of Object.entries(encounters)) {
      if (encounterData && encounterData.diagram) {
        if (_updateConnection(encounterData.diagram)) {
          console.log(`[ContentChangeManager] Updated connection in encounter: ${encounterName}`);
        }
      }
    }
  }


  /**
   * Handle when a new state is added
   * @param {string} emitter - 'game' | encounterName
   * @param {object} data - State persistence data
   */
  static handleStateAdded(emitter, data) {
    console.log(`[ContentChangeManager] State added in ${emitter}:`, data.id, data);
  }

  /**
   * Handle when a state is removed
   * @param {string} emitter - 'game' | encounterName
   * @param {object} data - State persistence data (or just { id })
   */
  static handleStateRemoved(emitter, data) {
    console.log(`[ContentChangeManager] State removed in ${emitter}:`, data.id, data);
  }

  /**
   * Handle when a connection is added
   * @param {string} emitter - 'game' | encounterName
   * @param {object} data - Connection persistence data
   */
  static handleConnectionAdded(emitter, data) {
    console.log(`[ContentChangeManager] Connection added in ${emitter}:`, data.id, data);
  }

  /**
   * Handle when a connection is removed
   * @param {string} emitter - 'game' | encounterName
   * @param {object} data - Connection persistence data (or just { id })
   */
  static handleConnectionRemoved(emitter, data) {
    console.log(`[ContentChangeManager] Connection removed in ${emitter}:`, data.id, data);
  }
}

export default ContentChangeManager;