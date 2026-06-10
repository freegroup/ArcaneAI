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
    welcomePrompt: '',
    gameTarget: '',
    helpText: '',
    finalPrompt: '',
    inventory: [],
    loading: false,
    error: null,
    gameName: null,
    hasUnsavedChanges: false
  },

  mutations: {
    SET_CONFIG(state, config) {
      state.personality = config.personality || ''
      state.welcomePrompt = config.welcome_prompt || ''
      state.gameTarget = config.game_target || ''
      state.helpText = config.help_text || ''
      state.inventory = config.inventory || []
      state.hasUnsavedChanges = false
    },
    SET_PERSONALITY(state, prompt) {
      state.personality = prompt
      state.hasUnsavedChanges = true
    },
    SET_WELCOME_PROMPT(state, prompt) {
      state.welcomePrompt = prompt
      state.hasUnsavedChanges = true
    },
    SET_GAME_TARGET(state, text) {
      state.gameTarget = text
      state.hasUnsavedChanges = true
    },
    SET_HELP_TEXT(state, text) {
      state.helpText = text
      state.hasUnsavedChanges = true
    },
    SET_INVENTORY(state, inventory) {
      state.inventory = inventory || []
      state.hasUnsavedChanges = true
    },
    ADD_INVENTORY_ITEM(state, item) {
      state.inventory = [...state.inventory, item]
      state.hasUnsavedChanges = true
    },
    REMOVE_INVENTORY_ITEM(state, index) {
      state.inventory = state.inventory.filter((_, i) => i !== index)
      state.hasUnsavedChanges = true
    },
    UPDATE_INVENTORY_ITEM(state, { index, item }) {
      const newInventory = [...state.inventory]
      newInventory[index] = item
      state.inventory = newInventory
      state.hasUnsavedChanges = true
    },
    SET_UNSAVED_CHANGES(state, value) {
      state.hasUnsavedChanges = value
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
        // RESTful: GET /games/{name}/config
        const response = await axios.get(`${API_BASE_URL}/games/${gameName}/config`)
        commit('SET_CONFIG', response.data)
      } catch (error) {
        if (error.response?.status === 404) {
          // Config existiert noch nicht - leere Config
          commit('SET_CONFIG', {
            personality: '',
            welcome_prompt: '',
            game_target: '',
            help_text: '',
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
     * Speichert die Config zum Server.
     *
     * Note: `personalities` (the legacy mood-dict) is intentionally NOT written here.
     * The backend migrates old maps to a single `personality` Jinja2 template on load,
     * and this save replaces the old structure on disk.
     */
    async saveConfig({ state, commit }) {
      if (!state.gameName) {
        throw new Error('No game name set')
      }

      const configData = {
        personality: state.personality,
        welcome_prompt: state.welcomePrompt,
        game_target: state.gameTarget,
        help_text: state.helpText,
        inventory: state.inventory
      }

      // RESTful: PUT /games/{name}/config with JSON body
      await axios.put(`${API_BASE_URL}/games/${state.gameName}/config`, configData)
      commit('SET_UNSAVED_CHANGES', false)
    },

    /**
     * Setzt die komplette Config (z.B. aus Migration)
     */
    setConfig({ commit }, config) {
      commit('SET_CONFIG', config)
    },

    setPersonality({ commit }, prompt) {
      commit('SET_PERSONALITY', prompt)
    },

    setWelcomePrompt({ commit }, prompt) {
      commit('SET_WELCOME_PROMPT', prompt)
    },

    setGameTarget({ commit }, text) {
      commit('SET_GAME_TARGET', text)
    },

    setHelpText({ commit }, text) {
      commit('SET_HELP_TEXT', text)
    },

    setInventory({ commit }, inventory) {
      commit('SET_INVENTORY', inventory)
    },

    addInventoryItem({ commit }, item) {
      commit('ADD_INVENTORY_ITEM', item)
    },

    removeInventoryItem({ commit }, index) {
      commit('REMOVE_INVENTORY_ITEM', index)
    },

    updateInventoryItem({ commit }, { index, item }) {
      commit('UPDATE_INVENTORY_ITEM', { index, item })
    }
  },

  getters: {
    personality: (state) => state.personality,
    welcomePrompt: (state) => state.welcomePrompt,
    gameTarget: (state) => state.gameTarget,
    helpText: (state) => state.helpText,
    finalPrompt: (state) => state.finalPrompt,
    inventory: (state) => state.inventory,
    inventoryCount: (state) => state.inventory.length,
    isLoading: (state) => state.loading,
    hasError: (state) => !!state.error,

    // Für Rückwärtskompatibilität
    gameConfig: (state) => ({
      personality: state.personality,
      welcome_prompt: state.welcomePrompt,
      game_target: state.gameTarget,
      help_text: state.helpText,
      inventory: state.inventory
    }),

    // Unsaved changes tracking
    hasUnsavedChanges: (state) => state.hasUnsavedChanges
  }
}
