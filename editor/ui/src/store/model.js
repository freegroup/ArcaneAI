/**
 * Model Store - Kanonisches Modell (states und connections OHNE Layout)
 * 
 * Das Model enthält die semantischen Daten aller States und Connections.
 * Layout-Informationen (x, y, vertex) werden in views.js gespeichert.
 * 
 * REFACTORED: 
 * - Entfernte ungenutzte Mutations (SET_STATES, SET_CONNECTIONS)
 * - Bug in removeDeletedElements gefixt
 * - Klarere Dokumentation
 */
import axios from 'axios'
import { nextTick } from 'vue'
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL

export default {
  namespaced: true,
  
  state: {
    states: {},       // id → state data (ohne x, y)
    connections: {},  // id → connection data (ohne vertex)
    loading: false,
    error: null,
    gameName: null,
    isPropertyUpdate: false  // Flag to prevent canvas refresh on property edits
  },

  mutations: {
    // ========== Core Mutations ==========
    /**
     * Set the complete model (states and connections)
     */
    SET_MODEL(state, { states, connections }) {
      state.states = states || {}
      state.connections = connections || {}
    },
    
    // ========== Single Item Mutations ==========
    /**
     * Add or update a single state
     */
    SET_STATE(state, stateData) {
      if (stateData?.id) {
        state.states = { ...state.states, [stateData.id]: stateData }
      }
    },
    
    /**
     * Add or update a single connection
     */
    SET_CONNECTION(state, connData) {
      if (connData?.id) {
        state.connections = { ...state.connections, [connData.id]: connData }
      }
    },
    
    /**
     * Remove a single state
     */
    REMOVE_STATE(state, stateId) {
      const newStates = { ...state.states }
      delete newStates[stateId]
      state.states = newStates
    },
    
    /**
     * Remove a single connection
     */
    REMOVE_CONNECTION(state, connId) {
      const newConnections = { ...state.connections }
      delete newConnections[connId]
      state.connections = newConnections
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
    },
    SET_PROPERTY_UPDATE(state, value) {
      state.isPropertyUpdate = value
    }
  },

  actions: {
    /**
     * Lädt das Model vom Server
     */
    async loadModel({ commit }, gameName) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      commit('SET_GAME_NAME', gameName)
      
      try {
        const response = await axios.get(`${API_BASE_URL}/game/${gameName}/model`)
        const modelData = response.data
        commit('SET_MODEL', {
          states: modelData.states || {},
          connections: modelData.connections || {}
        })
      } catch (error) {
        if (error.response?.status === 404) {
          commit('SET_MODEL', { states: {}, connections: {} })
        } else {
          commit('SET_ERROR', error.message)
          throw error
        }
      } finally {
        commit('SET_LOADING', false)
      }
    },

    /**
     * Speichert das Model zum Server
     */
    async saveModel({ state }) {
      console.log('[model.js] saveModel START', { gameName: state.gameName })
      if (!state.gameName) {
        console.error('[model.js] No gameName set!')
        throw new Error('Game name required to save model')
      }
      
      const modelData = {
        states: state.states,
        connections: state.connections
      }
      
      const blob = new Blob([JSON.stringify(modelData, null, 2)], { type: 'application/json' })
      const formData = new FormData()
      formData.append('file', blob, 'model.json')
      
      await axios.put(`${API_BASE_URL}/game/${state.gameName}/model`, formData)
      console.log('[model.js] saveModel COMPLETE')
    },

    /**
     * Setzt das komplette Model (z.B. aus Migration)
     */
    setModel({ commit }, { states, connections }) {
      commit('SET_MODEL', { states, connections })
    },

    /**
     * Merged Model-Updates vom Canvas.
     * Aktualisiert/fügt nur die übergebenen Elemente hinzu,
     * andere Elemente bleiben erhalten.
     */
    mergeModel({ commit, state }, { states, connections }) {
      const mergedStates = { ...state.states }
      for (const [id, stateData] of Object.entries(states || {})) {
        mergedStates[id] = stateData
      }
      
      const mergedConnections = { ...state.connections }
      for (const [id, connData] of Object.entries(connections || {})) {
        mergedConnections[id] = connData
      }
      
      commit('SET_MODEL', { states: mergedStates, connections: mergedConnections })
    },

    /**
     * Aktualisiert einen einzelnen State (von PropertyEditor).
     * Setzt isPropertyUpdate Flag um Canvas-Refresh zu verhindern.
     */
    updateState({ commit }, stateData) {
      commit('SET_PROPERTY_UPDATE', true)
      commit('SET_STATE', stateData)
      // Reset flag after Vue's reactivity cycle completes
      // Using double nextTick ensures all watchers have processed before flag is cleared
      nextTick(() => {
        nextTick(() => {
          commit('SET_PROPERTY_UPDATE', false)
        })
      })
    },

    /**
     * Aktualisiert einen einzelnen Trigger innerhalb eines States.
     * Findet den Parent-State über die Trigger-ID und aktualisiert nur diesen Trigger.
     * Setzt isPropertyUpdate Flag um Canvas-Refresh zu verhindern.
     * 
     * @param {Object} triggerData - Trigger-Daten mit id, text, userData etc.
     */
    updateTrigger({ commit, state }, triggerData) {
      if (!triggerData?.id) {
        console.warn('[model.js] updateTrigger: No trigger ID provided')
        return
      }
      
      // Find the parent state that contains this trigger
      let parentState = null
      let triggerIndex = -1
      
      for (const stateData of Object.values(state.states)) {
        if (stateData.trigger) {
          const idx = stateData.trigger.findIndex(t => t.id === triggerData.id)
          if (idx !== -1) {
            parentState = stateData
            triggerIndex = idx
            break
          }
        }
      }
      
      if (!parentState) {
        console.warn('[model.js] updateTrigger: Parent state not found for trigger', triggerData.id)
        return
      }
      
      // Create updated state with modified trigger
      const updatedState = {
        ...parentState,
        trigger: [...parentState.trigger]
      }
      
      // Update the specific trigger
      updatedState.trigger[triggerIndex] = {
        id: triggerData.id,
        name: triggerData.text,  // TriggerLabel uses 'text' for name
        description: triggerData.userData?.description,
        sound_effect: triggerData.userData?.sound_effect,
        sound_effect_duration: triggerData.userData?.sound_effect_duration,
        sound_effect_volume: triggerData.userData?.sound_effect_volume,
        system_prompt: triggerData.userData?.system_prompt,
        conditions: triggerData.userData?.conditions || [],
        actions: triggerData.userData?.actions || []
      }
      
      // Set flag and commit using proper mutation
      commit('SET_PROPERTY_UPDATE', true)
      commit('SET_STATE', updatedState)
      // Reset flag after Vue's reactivity cycle completes
      // Using double nextTick ensures all watchers have processed before flag is cleared
      nextTick(() => {
        nextTick(() => {
          commit('SET_PROPERTY_UPDATE', false)
        })
      })
    },

    /**
     * Entfernt einen State und alle zugehörigen Connections.
     * Cleanup in allen Views wird automatisch durchgeführt.
     */
    removeState({ commit, state, dispatch }, stateId) {
      // 1. Finde alle Connections die diesen State nutzen
      const connectionsToRemove = Object.values(state.connections)
        .filter(conn => 
          conn.source?.node === stateId || 
          conn.target?.node === stateId
        )
        .map(conn => conn.id)
      
      // 2. Entferne diese Connections (inkl. View-Cleanup)
      for (const connId of connectionsToRemove) {
        commit('REMOVE_CONNECTION', connId)
        dispatch('views/removeConnectionFromAllViews', connId, { root: true })
      }
      
      // 3. Entferne den State
      commit('REMOVE_STATE', stateId)
      
      // 4. Entferne State-Layout aus allen Views
      dispatch('views/removeStateFromAllViews', stateId, { root: true })
    },

    /**
     * Aktualisiert eine einzelne Connection (von PropertyEditor).
     * Setzt isPropertyUpdate Flag um Canvas-Refresh zu verhindern.
     */
    updateConnection({ commit }, connData) {
      commit('SET_PROPERTY_UPDATE', true)
      commit('SET_CONNECTION', connData)
      // Reset flag after Vue's reactivity cycle completes
      // Using double nextTick ensures all watchers have processed before flag is cleared
      nextTick(() => {
        nextTick(() => {
          commit('SET_PROPERTY_UPDATE', false)
        })
      })
    },

    /**
     * Entfernt eine Connection (inkl. View-Cleanup)
     */
    removeConnection({ commit, dispatch }, connId) {
      commit('REMOVE_CONNECTION', connId)
      dispatch('views/removeConnectionFromAllViews', connId, { root: true })
    }
  },

  getters: {
    allStates: (state) => Object.values(state.states),
    allConnections: (state) => Object.values(state.connections),
    getState: (state) => (id) => state.states[id],
    getConnection: (state) => (id) => state.connections[id],
    stateCount: (state) => Object.keys(state.states).length,
    connectionCount: (state) => Object.keys(state.connections).length,
    isLoading: (state) => state.loading,
    hasError: (state) => !!state.error,
    errorMessage: (state) => state.error
  }
}