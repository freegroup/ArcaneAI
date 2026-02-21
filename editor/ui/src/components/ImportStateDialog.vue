<template>
  <v-dialog v-model="dialogVisible" max-width="600" @update:model-value="onDialogChange">
    <v-card class="import-state-dialog">
      <DialogHeader 
        title="Import State" 
        icon="mdi-import"
        @close="close" 
      />

      <!-- Search Bar -->
      <div class="search-bar">
        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          placeholder="Search states..."
          density="compact"
          hide-details
          clearable
          variant="outlined"
          @click:clear="searchQuery = ''"
        ></v-text-field>
      </div>

      <v-card-text class="dialog-content">
        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
          <span>Loading states...</span>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredStates.length === 0" class="empty-state">
          <v-icon size="48" class="mb-2">mdi-file-document-outline</v-icon>
          <span v-if="searchQuery">No states found for "{{ searchQuery }}"</span>
          <span v-else>No states available to import</span>
        </div>

        <!-- State List -->
        <div v-else class="state-list">
          <div
            v-for="state in filteredStates"
            :key="state.id"
            :class="['state-item', 'state-item-clickable', { 'has-connection': state.hasDirectConnection }]"
            @click="importState(state)"
          >
            <div class="state-icon">
              <v-icon size="small">
                {{ state.hasDirectConnection ? 'mdi-circle' : 'mdi-circle-outline' }}
              </v-icon>
            </div>
            <div class="state-info">
              <span :class="['state-name', { 'connected-name': state.hasDirectConnection }]">
                {{ state.name }}
              </span>
              <span v-if="state.userData?.description" class="state-description">
                {{ truncate(state.userData.description, 60) }}
              </span>
            </div>
            <v-icon class="import-icon">mdi-import</v-icon>
          </div>
        </div>
      </v-card-text>

      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <v-btn class="btn-8bit btn-secondary" @click="close">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import DialogHeader from './DialogHeader.vue';
import { MessageTypes } from '../../public/shared/SharedConstants.js';
import ViewComposer from '../utils/ViewComposer.js';

export default {
  name: 'ImportStateDialog',
  
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },

  components: { DialogHeader },
  emits: ['update:modelValue'],

  data() {
    return {
      searchQuery: '',
      loading: false
    };
  },

  computed: {
    ...mapGetters('game', ['gameDiagram']),
    ...mapGetters('model', ['allStates']),
    ...mapGetters('views', ['currentView']),
    
    dialogVisible: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    },

    // Get all states from the World (game) diagram that are not yet in current view
    // Uses Overlay Pattern: checks views store for state IDs already in view
    gameStateNames() {
      if (!this.gameDiagram || !Array.isArray(this.gameDiagram)) {
        return [];
      }
      
      // Get IDs of states already in current view
      const statesInView = this.statesInCurrentView;
      
      // Filter for StateShape items only, excluding states already in view
      return this.gameDiagram
        .filter(item => item.type === 'StateShape')
        .filter(item => !statesInView.has(item.id))  // Exclude states by ID (new pattern)
        .map(state => ({
          id: state.id,
          name: state.name || 'Unnamed State',
          userData: state.userData || {},
          // Store full state data for import
          fullData: state
        }));
    },

    // IDs der States die bereits im aktuellen View sind
    statesInCurrentView() {
      const currentView = this.currentView;
      return new Set(Object.keys(currentView?.stateLayouts || {}));
    },

    // Prüft ob ein State eine direkte Connection zu einem State im aktuellen View hat
    statesWithDirectConnection() {
      const connections = this.$store.state.model.connections || {};
      const visibleStateIds = this.statesInCurrentView;
      const connectedStates = new Set();
      
      // Durchsuche alle Connections
      for (const conn of Object.values(connections)) {
        const sourceId = conn.source?.node;
        const targetId = conn.target?.node;
        
        // Wenn Source im View ist und Target nicht → Target ist verbunden
        if (visibleStateIds.has(sourceId) && !visibleStateIds.has(targetId)) {
          connectedStates.add(targetId);
        }
        // Wenn Target im View ist und Source nicht → Source ist verbunden
        if (visibleStateIds.has(targetId) && !visibleStateIds.has(sourceId)) {
          connectedStates.add(sourceId);
        }
      }
      
      return connectedStates;
    },

    // Search filtered states - erweitert um hasDirectConnection Flag
    filteredStates() {
      const connectedSet = this.statesWithDirectConnection;
      let states = this.gameStateNames.map(state => ({
        ...state,
        hasDirectConnection: connectedSet.has(state.id)
      }));
      
      // Sortiere: States mit Connection zuerst
      states.sort((a, b) => {
        if (a.hasDirectConnection && !b.hasDirectConnection) return -1;
        if (!a.hasDirectConnection && b.hasDirectConnection) return 1;
        return a.name.localeCompare(b.name);
      });
      
      if (!this.searchQuery) return states;
      
      const query = this.searchQuery.toLowerCase();
      return states.filter(state => 
        state.name.toLowerCase().includes(query) ||
        (state.userData?.description || '').toLowerCase().includes(query)
      );
    }
  },

  watch: {
    modelValue(newVal) {
      if (newVal) {
        // Dialog opened - reset state
        this.searchQuery = '';
        this.selectedState = null;
      }
    }
  },

  methods: {
    ...mapActions('views', ['addStateToView']),
    
    /**
     * Calculate the bounding box center of existing states in the current view.
     * Returns { x, y } of the center point, or a default if no states exist.
     */
    calculateBoundingBoxCenter() {
      const currentView = this.$store.getters['views/currentView'];
      const stateLayouts = currentView?.stateLayouts || {};
      const layoutValues = Object.values(stateLayouts);
      
      // Default position if no states exist yet
      if (layoutValues.length === 0) {
        return { x: 300, y: 200 };
      }
      
      // Calculate bounding box
      let minX = Infinity, maxX = -Infinity;
      let minY = Infinity, maxY = -Infinity;
      
      for (const layout of layoutValues) {
        minX = Math.min(minX, layout.x);
        maxX = Math.max(maxX, layout.x);
        minY = Math.min(minY, layout.y);
        maxY = Math.max(maxY, layout.y);
      }
      
      // Add some offset for the state width/height (approx 150x80)
      const stateWidth = 150;
      const stateHeight = 80;
      
      // Calculate center of bounding box
      const centerX = (minX + maxX + stateWidth) / 2;
      const centerY = (minY + maxY + stateHeight) / 2;
      
      // Add small random offset to avoid exact overlap
      const offsetX = (Math.random() - 0.5) * 50;
      const offsetY = (Math.random() - 0.5) * 30;
      
      return {
        x: Math.round(centerX + offsetX),
        y: Math.round(centerY + offsetY)
      };
    },

    /**
     * Import state from game diagram into current encounter.
     * Uses Overlay Pattern: Adds layout to current view, then composes full diagram.
     */
    importState(state) {
      const encounterName = this.$store.getters['encounters/currentEncounterName'];
      
      if (!encounterName) {
        console.warn('[ImportStateDialog] No current encounter set');
        this.close();
        return;
      }

      // Step 1: Find the original state in model by ID
      const originalState = this.$store.state.model.states[state.id];
      if (!originalState) {
        console.warn('[ImportStateDialog] State not found in model:', state.id);
        this.close();
        return;
      }

      // Step 2: Add layout for this state to current view
      // Position at center of existing states bounding box
      const layout = this.calculateBoundingBoxCenter();
      
      this.addStateToView({ stateId: state.id, layout });

      // Step 3: Compose full diagram (Model + View) and send to canvas
      // This ensures all connections are included!
      const model = {
        states: this.$store.state.model.states,
        connections: this.$store.state.model.connections
      };
      const view = this.$store.getters['views/currentView'];
      const composedDiagram = ViewComposer.compose(model, view);
      
      this.sendToCanvas(composedDiagram);
      
      this.close();
    },

    /**
     * Send document to canvas via parent window postMessage.
     * Uses unified message architecture: both Vue and Canvas communicate
     * through the parent window. Canvas listens on window.parent.
     */
    sendToCanvas(diagram) {
      window.postMessage({ 
        type: MessageTypes.V2C_SET_DOCUMENT, 
        data: JSON.parse(JSON.stringify(diagram)),
        source: 'ImportStateDialog'
      }, '*');
    },

    // Truncate text
    truncate(text, maxLength) {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },

    // Close dialog
    close() {
      this.dialogVisible = false;
    },

    // Handle dialog visibility change
    onDialogChange(value) {
      // Reset search when dialog closes
      if (!value) {
        this.searchQuery = '';
      }
    }
  }
};
</script>

<style scoped>
.import-state-dialog {
  background: var(--game-bg-primary);
  color: var(--game-text-primary);
}

.search-bar {
  padding: 12px 16px;
  border-bottom: 1px solid var(--game-border-color);
}

.dialog-content {
  padding: 0 !important;
  height: 350px;
  overflow-y: auto;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: var(--game-text-secondary);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--game-text-muted);
  gap: 8px;
}

/* State List */
.state-list {
  padding: 8px 0;
}

.state-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.15s;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.state-item:hover {
  background: var(--game-input-hover);
}

.state-item.selected {
  background: var(--game-accent-primary);
  color: var(--game-text-primary);
}

.state-icon {
  margin-right: 12px;
  color: var(--game-accent-secondary);
}

.state-item.selected .state-icon {
  color: var(--game-text-primary);
}

.state-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.state-name {
  font-weight: 500;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* States with direct connection - bold name only */
.connected-name {
  font-weight: 700;
}

.state-description {
  font-size: 12px;
  color: var(--game-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 2px;
}

.state-item.selected .state-description {
  color: var(--game-text-primary);
  opacity: 0.8;
}

.check-icon {
  color: var(--game-text-primary);
  margin-left: 8px;
}

/* Dialog Actions */
.dialog-actions {
  border-top: 1px solid var(--game-border-color);
  padding: 12px 16px;
  gap: 12px;
}

/* 8-bit Style Buttons */
.btn-8bit {
  font-family: var(--game-font-family-retro) !important;
  font-size: 12px !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  border-radius: 0 !important;
  padding: 8px 20px !important;
  min-width: 100px !important;
  height: 36px !important;
  transition: all var(--game-transition-fast) !important;
}

.btn-8bit.btn-primary {
  background: var(--game-accent-primary) !important;
  color: var(--game-text-primary) !important;
  box-shadow: inset -4px -4px 0px 0px #8c2022,
              0 0 0 3px black !important;
}

.btn-8bit.btn-primary:hover:not(:disabled) {
  background: var(--game-accent-tertiary) !important;
  box-shadow: inset -6px -6px 0px 0px #8c2022,
              0 0 0 3px black !important;
}

.btn-8bit.btn-primary:active:not(:disabled) {
  box-shadow: inset 4px 4px 0px 0px #8c2022,
              0 0 0 3px black !important;
}

.btn-8bit.btn-primary:disabled {
  background: var(--game-text-muted) !important;
  box-shadow: inset -4px -4px 0px 0px #555,
              0 0 0 3px #555 !important;
  opacity: 0.5 !important;
  cursor: not-allowed !important;
}

.btn-8bit.btn-secondary {
  background: var(--game-bg-secondary) !important;
  color: var(--game-text-primary) !important;
  box-shadow: inset -4px -4px 0px 0px #333,
              0 0 0 3px var(--game-border-color) !important;
}

.btn-8bit.btn-secondary:hover {
  background: var(--game-input-hover) !important;
  box-shadow: inset -6px -6px 0px 0px #333,
              0 0 0 3px var(--game-border-highlight) !important;
}

.btn-8bit.btn-secondary:active {
  box-shadow: inset 4px 4px 0px 0px #333,
              0 0 0 3px var(--game-border-color) !important;
}

/* Scrollbar styling */
.dialog-content::-webkit-scrollbar {
  width: 8px;
}

.dialog-content::-webkit-scrollbar-track {
  background: var(--game-bg-primary);
}

.dialog-content::-webkit-scrollbar-thumb {
  background: var(--game-border-color);
  border-radius: 4px;
}

.dialog-content::-webkit-scrollbar-thumb:hover {
  background: var(--game-text-muted);
}
</style>