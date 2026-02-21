/**
 * ViewComposer - Transformiert zwischen kanonischem Model und draw2d-Format
 * 
 * Das Model enthält States und Connections OHNE Layout-Informationen.
 * Views enthalten NUR Layout-Informationen (Positionen, Routing).
 * Der ViewComposer merged/splittet diese für die Canvas-Kommunikation.
 */
class ViewComposer {
  
  /**
   * Komponiert ein draw2d-kompatibles Diagram aus Model und View
   * 
   * NUR States die in der View ein Layout haben werden angezeigt!
   * Das ist das Overlay Pattern: Views sind Filter die bestimmen was sichtbar ist.
   * 
   * @param {Object} model - { states: {id: stateData}, connections: {id: connData} }
   * @param {Object} view - { stateLayouts: {id: {x, y}}, connectionRoutes: {id: {vertex: []}} }
   * @returns {Array} - draw2d JSON Array
   */
  static compose(model, view) {
    const diagram = []
    const stateLayouts = view?.stateLayouts || {}
    const connectionRoutes = view?.connectionRoutes || {}
    const rafts = view?.rafts || []
    
    // 0. Rafts zuerst (sind Hintergrund-Elemente)
    for (const raft of rafts) {
      diagram.push({
        type: 'Raft',
        id: raft.id,
        x: raft.x,
        y: raft.y,
        width: raft.width,
        height: raft.height,
        userData: raft.userData || {},
        labels: raft.labels || []
      })
    }
    
    // Set der States die in dieser View sichtbar sind
    const visibleStateIds = new Set(Object.keys(stateLayouts))
    
    // 1. NUR States mit Layout in der View werden angezeigt
    for (const [stateId, stateData] of Object.entries(model?.states || {})) {
      const layout = stateLayouts[stateId]
      // Skip states ohne Layout in dieser View
      if (!layout) continue
      
      diagram.push({
        ...stateData,
        x: layout.x,
        y: layout.y
      })
    }
    
    // 2. NUR Connections deren Source UND Target sichtbar sind
    for (const [connId, connData] of Object.entries(model?.connections || {})) {
      const sourceVisible = visibleStateIds.has(connData.source?.node)
      const targetVisible = visibleStateIds.has(connData.target?.node)
      
      // Skip connections wenn Source oder Target nicht sichtbar
      if (!sourceVisible || !targetVisible) continue
      
      const route = connectionRoutes[connId] || {}
      diagram.push({
        ...connData,
        vertex: route.vertex || []
      })
    }
    
    return diagram
  }
  
  /**
   * Extrahiert Model-Daten aus einem draw2d Diagram
   * OHNE Layout-Daten (x, y, vertex)
   * 
   * @param {Array} diagram - draw2d JSON Array
   * @returns {Object} - { states: {}, connections: {} }
   */
  static extractModel(diagram) {
    const model = { states: {}, connections: {} }
    
    for (const item of diagram || []) {
      if (item.type === 'TriggerConnection') {
        // Connection: Entferne Layout-Daten
        const connData = { ...item }
        delete connData.vertex
        delete connData.routingMetaData
        model.connections[item.id] = connData
      } else if (item.type === 'StateShape') {
        // State: Entferne Layout-Daten
        const stateData = { ...item }
        delete stateData.x
        delete stateData.y
        model.states[item.id] = stateData
      }
    }
    
    return model
  }
  
  /**
   * Extrahiert Layout-Daten aus einem draw2d Diagram
   * NUR Layout-Daten (x, y, vertex)
   * 
   * @param {Array} diagram - draw2d JSON Array
   * @returns {Object} - { stateLayouts: {}, connectionRoutes: {} }
   */
  static extractLayout(diagram) {
    const layout = { stateLayouts: {}, connectionRoutes: {}, rafts: [] }
    
    for (const item of diagram || []) {
      if (item.type === 'TriggerConnection') {
        layout.connectionRoutes[item.id] = {
          vertex: item.vertex || []
        }
      } else if (item.type === 'StateShape') {
        layout.stateLayouts[item.id] = {
          x: item.x,
          y: item.y
        }
      } else if (item.type === 'Raft') {
        layout.rafts.push({
          id: item.id,
          x: item.x,
          y: item.y,
          width: item.width,
          height: item.height,
          userData: item.userData || {},
          labels: item.labels || []
        })
      }
    }
    
    return layout
  }
  
  /**
   * Vergleicht zwei Models und gibt die Unterschiede zurück
   * 
   * @param {Object} oldModel - { states: {}, connections: {} }
   * @param {Object} newModel - { states: {}, connections: {} }
   * @returns {Object} - { states: { added, removed, changed }, connections: { added, removed, changed } }
   */
  static diffModels(oldModel, newModel) {
    const diff = {
      states: { added: [], removed: [], changed: [] },
      connections: { added: [], removed: [], changed: [] }
    }
    
    // States vergleichen
    const oldStateIds = new Set(Object.keys(oldModel?.states || {}))
    const newStateIds = new Set(Object.keys(newModel?.states || {}))
    
    for (const id of newStateIds) {
      if (!oldStateIds.has(id)) {
        diff.states.added.push(id)
      } else if (JSON.stringify(oldModel.states[id]) !== JSON.stringify(newModel.states[id])) {
        diff.states.changed.push(id)
      }
    }
    
    for (const id of oldStateIds) {
      if (!newStateIds.has(id)) {
        diff.states.removed.push(id)
      }
    }
    
    // Connections vergleichen
    const oldConnIds = new Set(Object.keys(oldModel?.connections || {}))
    const newConnIds = new Set(Object.keys(newModel?.connections || {}))
    
    for (const id of newConnIds) {
      if (!oldConnIds.has(id)) {
        diff.connections.added.push(id)
      } else if (JSON.stringify(oldModel.connections[id]) !== JSON.stringify(newModel.connections[id])) {
        diff.connections.changed.push(id)
      }
    }
    
    for (const id of oldConnIds) {
      if (!newConnIds.has(id)) {
        diff.connections.removed.push(id)
      }
    }
    
    return diff
  }
  
  /**
   * Prüft ob das Diagram leer ist
   * 
   * @param {Array} diagram - draw2d JSON Array
   * @returns {boolean}
   */
  static isEmpty(diagram) {
    return !diagram || diagram.length === 0
  }
  
  /**
   * Zählt States und Connections im Diagram
   * 
   * @param {Array} diagram - draw2d JSON Array
   * @returns {Object} - { states: number, connections: number }
   */
  static count(diagram) {
    let states = 0
    let connections = 0
    
    for (const item of diagram || []) {
      if (item.type === 'TriggerConnection') {
        connections++
      } else if (item.type === 'StateShape') {
        states++
      }
    }
    
    return { states, connections }
  }
  
  /**
   * Findet einen State/Connection by ID im Diagram
   * 
   * @param {Array} diagram - draw2d JSON Array
   * @param {string} id - ID des Elements
   * @returns {Object|null}
   */
  static findById(diagram, id) {
    return (diagram || []).find(item => item.id === id) || null
  }
  
  /**
   * Kopiert Layout von einer View zu einer anderen für ausgewählte States
   * 
   * @param {Object} sourceView - Quell-View
   * @param {Object} targetView - Ziel-View 
   * @param {Array} stateIds - IDs der zu kopierenden States
   * @returns {Object} - Aktualisierte Ziel-View
   */
  static copyLayoutToView(sourceView, targetView, stateIds) {
    const newView = { 
      ...targetView,
      stateLayouts: { ...targetView.stateLayouts },
      connectionRoutes: { ...targetView.connectionRoutes }
    }
    
    for (const stateId of stateIds) {
      if (sourceView.stateLayouts?.[stateId]) {
        newView.stateLayouts[stateId] = { ...sourceView.stateLayouts[stateId] }
      }
    }
    
    return newView
  }
}

export default ViewComposer