/**
 * Views Store - View Overlays (Layouts pro View)
 * 
 * Jede View enthält NUR Layout-Informationen (Positionen, Routing).
 * Die semantischen Daten kommen aus dem model.js Store.
 * 
 * REFACTORED: Redundante Mutations zusammengeführt
 * - SET_VIEW und UPDATE_VIEW → SET_VIEW (identisch)
 * - UPDATE_STATE_LAYOUT, UPDATE_CONNECTION_ROUTE, UPDATE_RAFTS → nutzen jetzt granulare Mutations
 * - UPDATE_CURRENT_VIEW_LAYOUT → PATCH_VIEW (unified)
 */
import axios from 'axios'
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL

export default {
  namespaced: true,
  
  state: {
    views: {},           // viewId → { viewId, viewType, stateLayouts, connectionRoutes, encounterConfig? }
    currentViewId: null, // 'world' oder 'encounter_xxx'
    loading: false,
    error: null,
    gameName: null
  },

  mutations: {
    // ========== Core Mutations ==========
    SET_VIEWS(state, views) {
      state.views = views || {}
    },
    
    /**
     * Set or update a complete view.
     * This is THE mutation for view updates.
     */
    SET_VIEW(state, { viewId, viewData }) {
      state.views = { ...state.views, [viewId]: viewData }
    },
    
    SET_CURRENT_VIEW(state, viewId) {
      state.currentViewId = viewId
    },
    
    // ========== Partial Update Mutations ==========
    /**
     * Patch multiple view properties at once.
     * More efficient than multiple single-property mutations.
     */
    PATCH_VIEW(state, { viewId, patch }) {
      const targetViewId = viewId || state.currentViewId
      if (!state.views[targetViewId]) return
      
      const view = { ...state.views[targetViewId] }
      
      if (patch.stateLayouts !== undefined) {
        view.stateLayouts = patch.stateLayouts
      }
      if (patch.connectionRoutes !== undefined) {
        view.connectionRoutes = patch.connectionRoutes
      }
      if (patch.rafts !== undefined) {
        view.rafts = patch.rafts
      }
      
      state.views = { ...state.views, [targetViewId]: view }
    },
    
    /**
     * Update a single state's layout in a view.
     */
    SET_STATE_LAYOUT(state, { viewId, stateId, layout }) {
      const targetViewId = viewId || state.currentViewId
      if (!state.views[targetViewId]) return
      
      const view = { ...state.views[targetViewId] }
      view.stateLayouts = { ...view.stateLayouts, [stateId]: layout }
      state.views = { ...state.views, [targetViewId]: view }
    },
    
    /**
     * Update a single connection's route in a view.
     */
    SET_CONNECTION_ROUTE(state, { viewId, connId, route }) {
      const targetViewId = viewId || state.currentViewId
      if (!state.views[targetViewId]) return
      
      const view = { ...state.views[targetViewId] }
      view.connectionRoutes = { ...view.connectionRoutes, [connId]: route }
      state.views = { ...state.views, [targetViewId]: view }
    },
    
    // ========== Remove Mutations ==========
    REMOVE_STATE_FROM_VIEW(state, { viewId, stateId }) {
      if (!state.views[viewId]?.stateLayouts) return
      
      const view = { ...state.views[viewId] }
      const newLayouts = { ...view.stateLayouts }
      delete newLayouts[stateId]
      view.stateLayouts = newLayouts
      state.views = { ...state.views, [viewId]: view }
    },
    
    REMOVE_CONNECTION_FROM_VIEW(state, { viewId, connId }) {
      if (!state.views[viewId]?.connectionRoutes) return
      
      const view = { ...state.views[viewId] }
      const newRoutes = { ...view.connectionRoutes }
      delete newRoutes[connId]
      view.connectionRoutes = newRoutes
      state.views = { ...state.views, [viewId]: view }
    },
    
    // ========== Status Mutations ==========
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    SET_GAME_NAME(state, name) {
      state.gameName = name
    }
  },

  actions: {
    /**
     * Lädt alle Views für ein Game
     */
    async loadAllViews({ commit }, gameName) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      commit('SET_GAME_NAME', gameName)
      
      try {
        const listResponse = await axios.get(`${API_BASE_URL}/game/${gameName}/views`)
        const viewNames = listResponse.data || []
        
        const views = {}
        
        for (const viewName of viewNames) {
          try {
            const viewResponse = await axios.get(`${API_BASE_URL}/game/${gameName}/views/${viewName}`)
            views[viewName] = viewResponse.data
          } catch (err) {
            console.warn(`Failed to load view ${viewName}:`, err)
          }
        }
        
        // World View als Default erstellen wenn nicht vorhanden
        if (!views['world']) {
          views['world'] = {
            viewId: 'world',
            viewType: 'world',
            stateLayouts: {},
            connectionRoutes: {}
          }
        }
        
        commit('SET_VIEWS', views)
      } catch (error) {
        if (error.response?.status === 404) {
          commit('SET_VIEWS', {
            world: {
              viewId: 'world',
              viewType: 'world',
              stateLayouts: {},
              connectionRoutes: {}
            }
          })
        } else {
          commit('SET_ERROR', error.message)
          throw error
        }
      } finally {
        commit('SET_LOADING', false)
      }
    },

    /**
     * Lädt eine einzelne View
     */
    async loadView({ commit, state }, { gameName, viewId }) {
      try {
        const response = await axios.get(`${API_BASE_URL}/game/${gameName || state.gameName}/views/${viewId}`)
        commit('SET_VIEW', { viewId, viewData: response.data })
      } catch (error) {
        if (error.response?.status !== 404) {
          throw error
        }
      }
    },

    /**
     * Speichert eine View zum Server
     */
    async saveView({ state }, { gameName, viewId }) {
      const targetGameName = gameName || state.gameName
      const targetViewId = viewId || state.currentViewId
      
      if (!targetGameName || !targetViewId) {
        throw new Error('Game name and view ID required')
      }
      
      const viewData = state.views[targetViewId]
      if (!viewData) {
        throw new Error(`View ${targetViewId} not found`)
      }
      
      const blob = new Blob([JSON.stringify(viewData, null, 2)], { type: 'application/json' })
      const formData = new FormData()
      formData.append('file', blob, `${targetViewId}.json`)
      
      await axios.put(`${API_BASE_URL}/game/${targetGameName}/views/${targetViewId}`, formData)
    },

    /**
     * Setzt die aktuelle View
     */
    setCurrentView({ commit }, viewId) {
      commit('SET_CURRENT_VIEW', viewId)
    },

    /**
     * Setzt eine View (z.B. aus Migration)
     */
    setView({ commit }, { viewId, viewData }) {
      commit('SET_VIEW', { viewId, viewData })
    },

    /**
     * Aktualisiert das Layout eines States in der aktuellen View
     */
    updateStateLayout({ commit, state }, { stateId, layout }) {
      commit('SET_STATE_LAYOUT', { viewId: state.currentViewId, stateId, layout })
    },

    /**
     * Aktualisiert das Routing einer Connection in der aktuellen View
     */
    updateConnectionRoute({ commit, state }, { connId, route }) {
      commit('SET_CONNECTION_ROUTE', { viewId: state.currentViewId, connId, route })
    },

    /**
     * Aktualisiert das komplette Layout der aktuellen View.
     * Uses unified PATCH_VIEW mutation.
     */
    updateCurrentViewLayout({ commit, state }, { stateLayouts, connectionRoutes, rafts }) {
      commit('PATCH_VIEW', { 
        viewId: state.currentViewId, 
        patch: { stateLayouts, connectionRoutes, rafts } 
      })
    },

    /**
     * Create a new encounter view
     */
    createEncounterView({ commit }, { encounterName }) {
      const viewId = `encounter_${encounterName}`
      const newView = {
        id: viewId,
        name: encounterName,
        type: 'encounter',
        stateLayouts: {},
        connectionRoutes: {}
      }
      commit('SET_VIEW', { viewId, viewData: newView })
      return viewId
    },
    
    /**
     * Add a state to the current view with layout.
     * Uses SET_STATE_LAYOUT for efficiency.
     */
    addStateToView({ commit, state }, { stateId, layout }) {
      if (!state.currentViewId || !state.views[state.currentViewId]) {
        console.warn('[views] addStateToView: No current view set')
        return
      }
      
      commit('SET_STATE_LAYOUT', { viewId: state.currentViewId, stateId, layout })
    },

    /**
     * Entfernt einen State aus allen Views
     */
    removeStateFromAllViews({ commit, state }, stateId) {
      for (const viewId of Object.keys(state.views)) {
        commit('REMOVE_STATE_FROM_VIEW', { viewId, stateId })
      }
    },
    
    /**
     * Entfernt eine Connection aus allen Views
     */
    removeConnectionFromAllViews({ commit, state }, connId) {
      for (const viewId of Object.keys(state.views)) {
        commit('REMOVE_CONNECTION_FROM_VIEW', { viewId, connId })
      }
    },

    /**
     * Entfernt einen State NUR aus der aktuellen View (nicht aus dem Model).
     * Für Encounter-Views: State wird aus View entfernt, bleibt aber im Model.
     */
    removeStateFromCurrentView({ commit, state }, stateId) {
      if (!state.currentViewId) return
      commit('REMOVE_STATE_FROM_VIEW', { viewId: state.currentViewId, stateId })
    },

    /**
     * Entfernt eine Connection NUR aus der aktuellen View (nicht aus dem Model).
     * Für Encounter-Views: Connection wird aus View entfernt, bleibt aber im Model.
     */
    removeConnectionFromCurrentView({ commit, state }, connId) {
      if (!state.currentViewId) return
      commit('REMOVE_CONNECTION_FROM_VIEW', { viewId: state.currentViewId, connId })
    },

    /**
     * Speichert alle Views
     */
    async saveAllViews({ state, dispatch }) {
      console.log('[views.js] saveAllViews START', { 
        gameName: state.gameName,
        viewCount: Object.keys(state.views).length,
        viewIds: Object.keys(state.views)
      })
      
      const targetGameName = state.gameName
      if (!targetGameName) {
        console.warn('[views.js] No gameName set, skipping saveAllViews')
        return
      }
      
      for (const viewId of Object.keys(state.views)) {
        try {
          console.log(`[views.js] Saving view: ${viewId}`)
          await dispatch('saveView', { gameName: targetGameName, viewId })
          console.log(`[views.js] View ${viewId} saved OK`)
        } catch (error) {
          console.error(`[views.js] Failed to save view ${viewId}:`, error)
        }
      }
      console.log('[views.js] saveAllViews COMPLETE')
    },

    /**
     * Löscht eine View
     */
    async deleteView({ commit, state }, { gameName, viewId }) {
      const targetGameName = gameName || state.gameName
      
      await axios.delete(`${API_BASE_URL}/game/${targetGameName}/views/${viewId}`)
      
      const newViews = { ...state.views }
      delete newViews[viewId]
      commit('SET_VIEWS', newViews)
      
      if (state.currentViewId === viewId) {
        commit('SET_CURRENT_VIEW', 'world')
      }
    },

    /**
     * Garbage Collection: Entfernt verwaiste Layouts.
     * Layouts die auf nicht mehr existierende Model-Einträge verweisen werden entfernt.
     * Gibt console.warn aus wenn verwaiste Einträge gefunden wurden.
     * 
     * @returns {Object} Report mit gefundenen verwaisten Einträgen
     */
    garbageCollectOrphanedLayouts({ commit, state, rootState }) {
      const modelStates = rootState.model?.states || {}
      const modelConnections = rootState.model?.connections || {}
      
      const orphanedReport = {
        stateLayouts: [],
        connectionRoutes: [],
        cleaned: false
      }
      
      // Durchsuche alle Views
      for (const [viewId, view] of Object.entries(state.views)) {
        const stateLayouts = view.stateLayouts || {}
        const connectionRoutes = view.connectionRoutes || {}
        
        // Finde verwaiste State-Layouts
        for (const stateId of Object.keys(stateLayouts)) {
          if (!modelStates[stateId]) {
            orphanedReport.stateLayouts.push({ viewId, stateId })
            commit('REMOVE_STATE_FROM_VIEW', { viewId, stateId })
          }
        }
        
        // Finde verwaiste Connection-Routes
        for (const connId of Object.keys(connectionRoutes)) {
          if (!modelConnections[connId]) {
            orphanedReport.connectionRoutes.push({ viewId, connId })
            commit('REMOVE_CONNECTION_FROM_VIEW', { viewId, connId })
          }
        }
      }
      
      // Log Warning wenn verwaiste Einträge gefunden
      const totalOrphaned = orphanedReport.stateLayouts.length + orphanedReport.connectionRoutes.length
      if (totalOrphaned > 0) {
        orphanedReport.cleaned = true
        console.warn(
          `[GC] Garbage Collection: ${totalOrphaned} verwaiste Layout-Einträge entfernt`,
          {
            stateLayouts: orphanedReport.stateLayouts,
            connectionRoutes: orphanedReport.connectionRoutes
          }
        )
      }
      
      return orphanedReport
    }
  },

  getters: {
    currentView: (state) => state.views[state.currentViewId],
    allViews: (state) => Object.values(state.views),
    viewById: (state) => (id) => state.views[id],
    currentStateLayouts: (state) => state.views[state.currentViewId]?.stateLayouts || {},
    currentConnectionRoutes: (state) => state.views[state.currentViewId]?.connectionRoutes || {},
    isWorldView: (state) => state.currentViewId === 'world',
    isEncounterView: (state) => state.currentViewId?.startsWith('encounter_'),
    encounterViews: (state) => Object.values(state.views).filter(v => v.viewType === 'encounter'),
    viewCount: (state) => Object.keys(state.views).length,
    isLoading: (state) => state.loading,
    hasError: (state) => !!state.error,
    
    /**
     * Generiert das Diagram für die World-View (Master-Sicht).
     * Kombiniert ALLE states/connections aus model mit worldView layouts.
     */
    getWorldDiagram: (state, getters, rootState) => {
      const worldView = state.views['world']
      if (!worldView) return []
      
      const modelStates = rootState.model?.states || {}
      const modelConnections = rootState.model?.connections || {}
      const stateLayouts = worldView.stateLayouts || {}
      const connectionRoutes = worldView.connectionRoutes || {}
      
      const diagram = []
      
      // 1. States mit Layout kombinieren
      for (const [stateId, stateData] of Object.entries(modelStates)) {
        const layout = stateLayouts[stateId] || { x: 100, y: 100 }
        diagram.push({
          ...stateData,
          x: layout.x,
          y: layout.y
        })
      }
      
      // 2. Connections mit Routing kombinieren
      for (const [connId, connData] of Object.entries(modelConnections)) {
        const route = connectionRoutes[connId] || {}
        diagram.push({
          ...connData,
          vertex: route.vertex || [],
          routingMetaData: route.routingMetaData
        })
      }
      
      return diagram
    },

    /**
     * Generiert das Diagram für eine Encounter-View.
     * Zeigt NUR die States/Connections die in dieser View sichtbar sind.
     * 
     * @param {string} encounterId - z.B. 'encounter_tavern'
     */
    getEncounterDiagram: (state, getters, rootState) => (encounterId) => {
      const encounterView = state.views[encounterId]
      if (!encounterView) return []
      
      const modelStates = rootState.model?.states || {}
      const modelConnections = rootState.model?.connections || {}
      const stateLayouts = encounterView.stateLayouts || {}
      const connectionRoutes = encounterView.connectionRoutes || {}
      
      const diagram = []
      
      // 1. NUR States mit Layout in dieser View
      for (const [stateId, layout] of Object.entries(stateLayouts)) {
        const stateData = modelStates[stateId]
        if (stateData) {
          diagram.push({
            ...stateData,
            x: layout.x,
            y: layout.y
          })
        }
      }
      
      // 2. NUR Connections mit Route in dieser View
      for (const [connId, route] of Object.entries(connectionRoutes)) {
        const connData = modelConnections[connId]
        if (connData) {
          diagram.push({
            ...connData,
            vertex: route.vertex || [],
            routingMetaData: route.routingMetaData
          })
        }
      }
      
      return diagram
    }
  }
}
