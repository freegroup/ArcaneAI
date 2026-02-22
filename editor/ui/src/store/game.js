/**
 * Game Store - Orchestrator for Loading/Saving Games
 * 
 * RESPONSIBILITIES:
 * - Orchestration of load/save across all stores
 * - Maintaining gameName as single source of truth
 * - Loading/error status tracking
 * 
 * DATA STORES (separated by concern):
 * - Config (prompts, inventory) → config.js
 * - States/Connections → model.js
 * - Layout/Positions → views.js
 * - Encounter metadata → encounters.js
 */

export default {
  namespaced: true,
  
  state: {
    gameName: "unknown",
    loading: false,
    error: null,
  },
  
  mutations: {
    SET_LOADING(state, isLoading) {
      state.loading = isLoading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
    SET_GAME_NAME(state, newName) {
      state.gameName = newName;
    },
  },
  
  actions: {
    /**
     * Initialisiert den Game Store.
     * Placeholder für zukünftige Initialisierungslogik.
     */
    async initialize() {
      // Placeholder for future initialization
    },

    /**
     * Lädt ein komplettes Game.
     * Orchestriert: config, model, views, sounds, encounters
     */
    async loadGame({ commit, dispatch }, gameName) {
      if (!gameName || gameName.length === 0) {
        return;
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      commit('SET_GAME_NAME', gameName);
      
      try {
        // 1. Lade Config
        await dispatch('config/loadConfig', gameName, { root: true });
        
        // 2. Lade Model (States + Connections)
        await dispatch('model/loadModel', gameName, { root: true });
        
        // 3. Lade Views (Layouts)
        await dispatch('views/loadAllViews', gameName, { root: true });
        
        // 4. Garbage Collection: Entferne verwaiste Layouts
        // (Layouts die auf nicht mehr existierende Model-Einträge verweisen)
        dispatch('views/garbageCollectOrphanedLayouts', null, { root: true });
        
        // 5. Lade Related Resources
        await dispatch('sounds/fetchSounds', gameName, { root: true });
        await dispatch('encounters/fetchEncounters', gameName, { root: true });
        
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error loading game');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    /**
     * Speichert das komplette Game.
     * Orchestriert: config, model, views
     */
    async saveGame({ commit, state, dispatch }) {
      console.log('[game.js] saveGame START', { gameName: state.gameName });
      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      
      try {
        // 1. Save Config
        await dispatch('config/saveConfig', null, { root: true });
        
        // 2. Save Model (States + Connections)
        await dispatch('model/saveModel', null, { root: true });
        
        // 3. Save Views (Layouts)
        await dispatch('views/saveAllViews', null, { root: true });
        
        console.log('[game.js] saveGame COMPLETE');
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error saving game');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

  },
  
  getters: {
    gameName: (state) => state.gameName,
    isLoading: (state) => state.loading,
    error: (state) => state.error,
    
    // Diagram wird aus model + views zusammengebaut
    gameDiagram: (state, getters, rootState, rootGetters) => {
      return rootGetters['views/getWorldDiagram'] || [];
    },
    
    /**
     * Zentrales hasUnsavedChanges - prüft ALLE relevanten Stores
     */
    hasUnsavedChanges: (state, getters, rootState, rootGetters) => {
      const modelUnsaved = rootGetters['model/hasUnsavedChanges'] || false;
      const configUnsaved = rootGetters['config/hasUnsavedChanges'] || false;
      // Views könnten auch Änderungen haben (positions etc.)
      // const viewsUnsaved = rootGetters['views/hasUnsavedChanges'] || false;
      return modelUnsaved || configUnsaved;
    },
  },
};