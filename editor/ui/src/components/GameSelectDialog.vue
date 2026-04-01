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
        <ThemedButton @click="closeDialog" variant="secondary">
          Cancel
        </ThemedButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
import DialogHeader from './DialogHeader.vue';
import ThemedButton from './ThemedButton.vue';

export default {
  components: { DialogHeader, ThemedButton },
  props: {
    dialog: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    ...mapGetters('games', ['games']),
    maps() {
      return this.games.filter(g => g !== 'template');
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
.scrollable-list {
  overflow-y: auto;
}

.scrollable-list ul {
  list-style: none;
}

.scrollable-list li {
  cursor: pointer;
  box-sizing: border-box;
}
</style>