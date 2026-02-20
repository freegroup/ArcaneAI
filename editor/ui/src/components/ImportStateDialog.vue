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
            class="state-item state-item-clickable"
            @click="importState(state)"
          >
            <div class="state-icon">
              <v-icon size="small">mdi-circle-slice-8</v-icon>
            </div>
            <div class="state-info">
              <span class="state-name">{{ state.name }}</span>
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
import CCM from '../utils/ContentChangeManager.js';
import { MessageTypes } from '../../public/shared/SharedConstants.js';

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
    ...mapGetters('encounters', ['currentEncounter']),
    
    dialogVisible: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    },

    // Get state names already in the current encounter (from store)
    encounterStateNames() {
      if (!this.currentEncounter?.diagram || !Array.isArray(this.currentEncounter.diagram)) {
        return new Set();
      }
      
      // Collect all state names from the encounter diagram
      return new Set(
        this.currentEncounter.diagram
          .filter(item => item.type === 'StateShape')
          .map(item => item.name)
      );
    },

    // Get all states from the World (game) diagram that are not yet in encounter
    gameStateNames() {
      if (!this.gameDiagram || !Array.isArray(this.gameDiagram)) {
        return [];
      }
      
      // Filter for StateShape items only, excluding states already in encounter
      return this.gameDiagram
        .filter(item => item.type === 'StateShape')
        .filter(item => !this.encounterStateNames.has(item.name))  // Exclude existing states
        .map(state => ({
          id: state.id,
          name: state.name || 'Unnamed State',
          userData: state.userData || {},
          // Store full state data for import
          fullData: state
        }));
    },

    // Search filtered states
    filteredStates() {
      if (!this.searchQuery) return this.gameStateNames;
      
      const query = this.searchQuery.toLowerCase();
      return this.gameStateNames.filter(state => 
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
    ...mapActions('encounters', ['updateEncounterDiagram']),
    
    /**
     * Import state from game diagram into current encounter
     * 1. Find state in gameDiagram by ID
     * 2. Add copy at beginning of encounter diagram
     * 3. Notify CCM about state addition
     * 4. Send updated diagram to canvas
     */
    importState(state) {
      const encounterName = this.$store.getters['encounters/currentEncounterName'];
      
      if (!encounterName) {
        console.warn('[ImportStateDialog] No current encounter set');
        this.close();
        return;
      }

      // Step 1: Find the original state in game diagram by ID
      const originalState = this.gameDiagram?.find(item => item.id === state.id);
      if (!originalState) {
        console.warn('[ImportStateDialog] State not found in game diagram:', state.id);
        this.close();
        return;
      }

      // Step 2: Create deep copy with new position for encounter
      const stateCopy = JSON.parse(JSON.stringify(originalState));
      //stateCopy.x = 100 + Math.random() * 300;  // Random position in visible area
      //stateCopy.y = 100 + Math.random() * 200;

      // Step 3: Insert at BEGINNING of encounter diagram
      const currentDiagram = this.currentEncounter?.diagram ? [...this.currentEncounter.diagram] : [];
      currentDiagram.unshift(stateCopy);  // Add at beginning
      
      // Step 4: Update store
      this.updateEncounterDiagram({ encounterName, diagram: currentDiagram });
      
      // Step 5: Notify CCM about state addition
      CCM.handleStateAdded(encounterName, stateCopy);

      // Step 6: Get fresh diagram from store and send to canvas
      const updatedDiagram = this.$store.getters['encounters/currentEncounterDiagram'];
      this.sendToCanvas(updatedDiagram);
      
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