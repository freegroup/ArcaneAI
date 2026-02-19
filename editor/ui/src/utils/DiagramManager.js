/**
 * DiagramManager
 * 
 * Central manager for all diagram operations across world and encounter views.
 * Handles state and connection management transparently.
 */
class DiagramManager {
  constructor(store) {
    this.store = store;
  }

  /**
   * Get all states that can be imported into an encounter
   * Returns states from world that are not yet in the encounter
   * 
   * @param {string} encounterName - Name of the encounter
   * @returns {Array} Array of state objects that can be imported
   */
  getImportableStates(encounterName) {
    // Get world states from game store
    const worldDiagram = this.store.getters['game/gameDiagram'];
    if (!worldDiagram || !Array.isArray(worldDiagram)) {
      return [];
    }
    
    const worldStates = worldDiagram.filter(item => item.type === 'StateShape');
    
    // Get encounter states
    const encounterData = this.store.getters['encounters/getEncounterData'](encounterName);
    if (!encounterData || !encounterData.diagram) {
      // If encounter has no diagram yet, all world states can be imported
      return worldStates;
    }
    
    const encounterStates = encounterData.diagram.filter(item => item.type === 'StateShape');
    const encounterStateIds = encounterStates.map(s => s.id);
    
    // Return world states that are not in the encounter
    return worldStates.filter(state => !encounterStateIds.includes(state.id));
  }

  /**
   * Import a state into an encounter
   * Automatically includes relevant connections where both source and target exist
   * 
   * @param {string} encounterName - Name of the encounter
   * @param {string} stateId - ID of the state to import
   * @returns {Promise} Resolves when import is complete
   */
  async importState(encounterName, stateId) {
    const encounterData = this.store.getters['encounters/getEncounterData'](encounterName);
    const gameName = this.store.getters['game/gameName'];
    
    if (!encounterData || !gameName) {
      throw new Error('Encounter or game not found');
    }
    
    // Get the state from world
    const worldDiagram = this.store.getters['game/gameDiagram'];
    const stateToImport = worldDiagram.find(item => 
      item.type === 'StateShape' && item.id === stateId
    );
    
    if (!stateToImport) {
      throw new Error(`State with id ${stateId} not found in world`);
    }
    
    // Clone the state (deep copy to avoid reference issues)
    const clonedState = JSON.parse(JSON.stringify(stateToImport));
    
    // Get current encounter diagram
    const currentDiagram = encounterData.diagram || [];
    
    // Get all state IDs that will be in encounter after import
    const encounterStateIds = currentDiagram
      .filter(item => item.type === 'StateShape')
      .map(s => s.id);
    encounterStateIds.push(stateId);
    
    // Find connections in world where both source AND target are in the encounter
    const worldConnections = worldDiagram.filter(item => item.type === 'TriggerConnection');
    const relevantConnections = worldConnections.filter(conn => {
      const sourceId = conn.source?.node;
      const targetId = conn.target?.node;
      return encounterStateIds.includes(sourceId) && encounterStateIds.includes(targetId);
    });
    
    // Get connections already in encounter
    const encounterConnectionIds = currentDiagram
      .filter(item => item.type === 'TriggerConnection')
      .map(c => c.id);
    
    // Find new connections to add (not already in encounter)
    const connectionsToAdd = relevantConnections.filter(
      conn => !encounterConnectionIds.includes(conn.id)
    );
    
    // Clone connections
    const clonedConnections = connectionsToAdd.map(conn => 
      JSON.parse(JSON.stringify(conn))
    );
    
    // Create new diagram with imported state and connections
    const newDiagram = [
      ...currentDiagram,
      clonedState,
      ...clonedConnections
    ];
    
    // Update encounter data
    const updatedEncounterData = {
      ...encounterData,
      diagram: newDiagram
    };
    
    // Save via encounters store
    await this.store.dispatch('encounters/updateEncounter', {
      gameName,
      encounterName,
      data: updatedEncounterData
    });
    
    return {
      stateImported: clonedState,
      connectionsAdded: clonedConnections,
      totalItems: newDiagram.length
    };
  }
}

// Export singleton instance factory
let instance = null;

export function createDiagramManager(store) {
  if (!instance) {
    instance = new DiagramManager(store);
  }
  return instance;
}

export function getDiagramManager() {
  if (!instance) {
    throw new Error('DiagramManager not initialized. Call createDiagramManager first.');
  }
  return instance;
}