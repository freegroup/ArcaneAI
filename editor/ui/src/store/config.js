/**
 * Config Store - Game-Konfiguration (Prompts, Inventory)
 * 
 * Enthält die Konfiguration eines Spiels, die unabhängig vom Model ist.
 */
import axios from 'axios'
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL

export default {
  namespaced: true,
  
  state: {
    personality: '',
    finalPrompt: '',
    inventory: [],
    loading: false,
    error: null,
    gameName: null
  },

  mutations: {
    SET_CONFIG(state, config) {
      state.personality = config.personality || ''
      state.inventory = config.inventory || []
    },
    SET_PERSONALITY(state, prompt) {
      state.personality = prompt
    },
    SET_INVENTORY(state, inventory) {
      state.inventory = inventory || []
    },
    ADD_INVENTORY_ITEM(state, item) {
      state.inventory = [...state.inventory, item]
    },
    REMOVE_INVENTORY_ITEM(state, index) {
      state.inventory = state.inventory.filter((_, i) => i !== index)
    },
    UPDATE_INVENTORY_ITEM(state, { index, item }) {
      const newInventory = [...state.inventory]
      newInventory[index] = item
      state.inventory = newInventory
    },
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
     * Lädt die Config vom Server
     */
    async loadConfig({ commit }, gameName) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      commit('SET_GAME_NAME', gameName)
      
      try {
        const response = await axios.get(`${API_BASE_URL}/game/${gameName}/config`)
        commit('SET_CONFIG', response.data)
      } catch (error) {
        if (error.response?.status === 404) {
          // Config existiert noch nicht - leere Config
          commit('SET_CONFIG', {
            personality: '',
            inventory: []
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
     * Speichert die Config zum Server
     */
    async saveConfig({ state }) {
      if (!state.gameName) {
        throw new Error('No game name set')
      }
      
      const configData = {
        personality: state.personality,
        inventory: state.inventory
      }
      
      const blob = new Blob([JSON.stringify(configData, null, 2)], { type: 'application/json' })
      const formData = new FormData()
      formData.append('file', blob, 'config.json')
      
      await axios.put(`${API_BASE_URL}/game/${state.gameName}/config`, formData)
    },

    /**
     * Setzt die komplette Config (z.B. aus Migration)
     */
    setConfig({ commit }, config) {
      commit('SET_CONFIG', config)
    },

    /**
     * Aktualisiert die Personality
     */
    setPersonality({ commit }, prompt) {
      commit('SET_PERSONALITY', prompt)
    },

    /**
     * Aktualisiert das Inventory
     */
    setInventory({ commit }, inventory) {
      commit('SET_INVENTORY', inventory)
    },

    /**
     * Fügt ein Item zum Inventory hinzu
     */
    addInventoryItem({ commit }, item) {
      commit('ADD_INVENTORY_ITEM', item)
    },

    /**
     * Entfernt ein Item aus dem Inventory
     */
    removeInventoryItem({ commit }, index) {
      commit('REMOVE_INVENTORY_ITEM', index)
    },

    /**
     * Aktualisiert ein Inventory Item
     */
    updateInventoryItem({ commit }, { index, item }) {
      commit('UPDATE_INVENTORY_ITEM', { index, item })
    }
  },

  getters: {
    personality: (state) => state.personality,
    finalPrompt: (state) => state.finalPrompt,
    inventory: (state) => state.inventory,
    inventoryCount: (state) => state.inventory.length,
    isLoading: (state) => state.loading,
    hasError: (state) => !!state.error,
    
    // Für Rückwärtskompatibilität
    gameConfig: (state) => ({
      personality: state.personality,
      inventory: state.inventory
    })
  }
}