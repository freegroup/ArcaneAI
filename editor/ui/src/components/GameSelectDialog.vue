<template>
  <v-dialog :model-value="dialog" max-width="600" @click:outside="closeDialog" @update:model-value="updateDialog">
    <v-card class="game-select-dialog">
      <DialogHeader 
        title="Select a Game" 
        @close="closeDialog" 
      />
      <v-card-text class="dialog-content">
        <div class="scrollable-list">
          <ul>
            <li
              v-for="(map, index) in maps"
              :key="index"
              @click="selectMap(map)"
              class="clickable-item"
            >
              {{ map }}
            </li>
          </ul>
        </div>
      </v-card-text>
      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <RetroButton @click="closeDialog" variant="secondary">
          Cancel
        </RetroButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
import DialogHeader from './DialogHeader.vue';
import RetroButton from './RetroButton.vue';

export default {
  components: { DialogHeader, RetroButton },
  props: {
    dialog: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    ...mapGetters('games', ['games']),
    maps() {
      return this.games;
    },
  },
  methods: {
    ...mapActions('games', ['fetchGames', 'selectGame']),

    async loadMaps() {
      await this.fetchGames();
    },

    async selectMap(map) {
      // Select and load the game via games store, which loads it into game store
      await this.selectGame(map);
      // Navigate to the game's world view
      this.$router.push({ name: 'world', params: { gameName: map } });
      this.$emit('update:dialog', false); // Close the dialog
    },

    closeDialog() {
      this.$emit('update:dialog', false); // Close the dialog
    },

    updateDialog(value) {
      this.$emit('update:dialog', value); // Update dialog state in parent
    },
  },
  watch: {
    dialog(value) {
      if (value) {
        this.loadMaps(); // Load maps when dialog opens
      }
    },
  },
};
</script>

<style scoped>
/* Override Vuetify defaults */
.game-select-dialog :deep(.v-card) {
  background: var(--game-bg-secondary) !important;
  color: var(--game-text-primary) !important;
}

.game-select-dialog {
  background: var(--game-bg-secondary);
  color: var(--game-text-primary);
  border: 2px solid var(--game-border-highlight);
  border-radius: var(--game-radius-lg);
  box-shadow: var(--game-shadow-lg);
}


.dialog-content {

  background: var(--game-bg-secondary);
}

/* Scrollable List */
.scrollable-list {
  min-height: 300px;
  max-height: 400px;
  overflow-y: auto;
  background: var(--game-bg-primary);
  border: 2px solid var(--game-border-color);
  border-radius: var(--game-radius-md);

  margin: 0;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
}

/* Scrollbar Styling */
.scrollable-list::-webkit-scrollbar {
  width: 12px;
}

.scrollable-list::-webkit-scrollbar-track {
  background: var(--game-bg-tertiary);
  border-radius: var(--game-radius-sm);
}

.scrollable-list::-webkit-scrollbar-thumb {
  background: var(--game-accent-primary);
  border-radius: var(--game-radius-sm);
  border: 2px solid var(--game-bg-tertiary);
}

.scrollable-list::-webkit-scrollbar-thumb:hover {
  background: var(--game-accent-tertiary);
  box-shadow: 0 0 8px var(--game-accent-primary);
}

.scrollable-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

/* List Items - 8-Bit Style */
.scrollable-list li {
  cursor: pointer;
  background: var(--game-bg-secondary);
  border: 2px solid transparent; /* Always present to prevent layout shift */
  padding: 12px 16px; /* Added padding for better look and stability */
  margin-bottom: 4px;
  color: var(--game-text-primary);
  font-size: var(--game-font-size-md);
  letter-spacing: 4px;
  transition: all var(--game-transition-fast);
  box-sizing: border-box;
}

.scrollable-list li:hover {
  background: var(--game-input-hover);
  border-color: var(--game-accent-primary);
  color: var(--game-accent-secondary);
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.2);
}

.scrollable-list li:active {
  background: var(--game-accent-primary);
  color: var(--game-text-primary);
}

.dialog-actions {
  border-top: 1px solid var(--game-border-color);
  background: var(--game-bg-tertiary);
}

.dialog-actions .retro-btn {
  margin-left: var(--game-spacing-md);
}
</style>