/**
 * Game Store - Orchestriert Game-Laden und verwaltet Game-Config
 * 
 * VERANTWORTLICHKEITEN:
 * 1. Game-Config (system_prompt, final_prompt, inventory)
 * 2. Orchestrierung von Load/Save über alle Stores
 * 
 * DATEN-STORES (ausgelagert):
 * - States/Connections → model.js
 * - Layout/Positions → views.js
 */

export default {
  namespaced: true,
  
  state: {
    gameConfig: {
      system_prompt: "game prompt",
      final_prompt: "final prompt",
      inventory: [],
    },
    gameName: "unknown",
    loading: false,
    error: null,
  },
  
  mutations: {
    SET_GAME_CONFIG(state, data) {
      state.gameConfig = data;
    },
    ADD_INVENTORY_ITEM(state, item) {
      state.gameConfig.inventory.push(item);
    },
    UPDATE_INVENTORY_ITEM(state, { index, item }) {
      state.gameConfig.inventory.splice(index, 1, item);
    },
    REMOVE_INVENTORY_ITEM(state, index) {
      state.gameConfig.inventory.splice(index, 1);
    },
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
        
        // Config aus config-store übernehmen
        const config = this.state.config;
        commit('SET_GAME_CONFIG', {
          system_prompt: config.system_prompt,
          final_prompt: config.final_prompt,
          inventory: config.inventory || [],
        });
        
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

    // ========== Config Actions ==========
    updateGameConfig({ commit, dispatch }, data) {
      commit('SET_GAME_CONFIG', data);
      // Sync to config store
      dispatch('config/setConfig', data, { root: true });
    },
    
    // ========== Inventory Actions ==========
    addInventoryItem({ commit }, item) {
      commit('ADD_INVENTORY_ITEM', item);
    },
    
    updateInventoryItem({ commit }, { index, item }) {
      commit('UPDATE_INVENTORY_ITEM', { index, item });
    },
    
    removeInventoryItem({ commit }, index) {
      commit('REMOVE_INVENTORY_ITEM', index);
    },
  },
  
  getters: {
    gameConfig: (state) => state.gameConfig,
    gameName: (state) => state.gameName,
    isLoading: (state) => state.loading,
    error: (state) => state.error,
    
    // Diagram wird aus model + views zusammengebaut
    gameDiagram: (state, getters, rootState, rootGetters) => {
      return rootGetters['views/getWorldDiagram'] || [];
    },
  },
};