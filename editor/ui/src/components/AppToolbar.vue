<template>
  <v-app-bar border dark class="app-toolbar">
    
    <ThemedButton @click="newFileDialog" variant="secondary">New Game</ThemedButton>
    <ThemedButton @click="openFileDialog" variant="secondary">Load Game</ThemedButton>
    <ThemedButton @click="save" variant="secondary">Save Game</ThemedButton>
    <ThemedButton @click="newEncounterDialog" variant="secondary">Add Encounter</ThemedButton>
    
    <v-spacer></v-spacer>

    <GameSelectDialog v-model:dialog="gameSelectDialog" />
    <GameNewDialog    v-model:dialog="gameNewDialog" />
    <EncounterNewDialog v-model="encounterNewDialog" />
  </v-app-bar>
</template>

<script>
import { mapActions } from 'vuex';
import GameNewDialog from './GameNewDialog.vue';
import GameSelectDialog from './GameSelectDialog.vue';
import EncounterNewDialog from './EncounterNewDialog.vue';
import ThemedButton from './ThemedButton.vue';

export default {
  components: {
    GameSelectDialog,
    GameNewDialog,
    EncounterNewDialog,
    ThemedButton,
  },
  data() {
    return {
      gameSelectDialog: false,
      gameNewDialog: false,
      encounterNewDialog: false,
    };
  },
  methods: {
    ...mapActions('game', ['saveGame']),
    
    newFileDialog() {
      this.gameNewDialog = true;
    },
    
    openFileDialog() {
      this.gameSelectDialog = true;
    },
    
    save() {
      console.log("Save Game");
      this.saveGame();
    },
    
    newEncounterDialog() {
      this.encounterNewDialog = true;
    },
  },
};
</script>

<style>
/* Structural layout only — visual styles in theme files */

.app-toolbar.v-toolbar {
  overflow: visible !important;
}

.app-toolbar .v-toolbar__content {
  overflow: visible !important;
}
</style>