<template>
  <v-app-bar border dark class="app-toolbar">
    
    <RetroButton @click="newFileDialog" variant="secondary">New Game</RetroButton>
    <RetroButton @click="openFileDialog" variant="secondary">Load Game</RetroButton>
    <RetroButton @click="save" variant="secondary">Save Game</RetroButton>
    <RetroButton @click="newEncounterDialog" variant="secondary">Add Encounter</RetroButton>
    
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
import RetroButton from './RetroButton.vue';

export default {
  components: {
    GameSelectDialog,
    GameNewDialog,
    EncounterNewDialog,
    RetroButton,
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
/* Remove scoped to ensure styles apply */

/* Override Vuetify App Bar - Fixed height of 48px */
.v-toolbar {
  background: linear-gradient(135deg, var(--game-bg-tertiary) 0%, #0a0a14 100%) !important;
  border-bottom: 3px solid var(--game-accent-primary) !important;
  border-top: 2px solid var(--game-accent-secondary) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6), 
              inset 0 -2px 0 rgba(0, 0, 0, 0.4) !important;
  overflow: visible !important;
}

.v-toolbar__content {
  background: transparent !important;
  overflow: visible !important;
}

/* Toolbar Retro Buttons */
.app-toolbar .retro-btn {
  margin: 0 var(--game-spacing-sm) !important;
}
</style>