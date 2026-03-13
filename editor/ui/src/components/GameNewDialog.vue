<template>
  <v-dialog :model-value="dialog" max-width="500" @click:outside="closeDialog" @update:model-value="updateDialog">
    <v-card class="game-new-dialog">
      <DialogHeader
        title="Create Game"
        @close="closeDialog"
      />
      <v-card-text class="dialog-content">
        <p class="dialog-description">
          Every legend begins with a single step. Name your world and bring a new adventure to life.
        </p>
        <v-text-field
          ref="nameInput"
          label="Name"
          v-model="mapName"
          :error-messages="nameError"
          @input="validateName"
        ></v-text-field>
      </v-card-text>
      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <ThemedButton @click="closeDialog" variant="secondary">
          Cancel
        </ThemedButton>
        <ThemedButton 
          @click="createDialog" 
          :disabled="isCreateDisabled" 
        >
          Create
        </ThemedButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapActions, mapGetters } from "vuex";
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
  data() {
    return {
      mapName: "", // Name for the map
      nameError: "", // Error message for the input field
    };
  },
  computed: {
    ...mapGetters("games", ["games"]),
    maps() {
      return this.games;
    },
    isCreateDisabled() {
      return !this.mapName || this.maps.includes(this.mapName);
    },
  },
  methods: {
    ...mapActions("games", ["fetchGames", "createNewGame"]),

    async loadMaps() {
      await this.fetchGames();
    },

  

    validateName() {
      if (this.maps.includes(this.mapName)) {
        this.nameError = "Name already exists.";
      } else {
        this.nameError = "";
      }
    },

    async createDialog() {
      if (!this.isCreateDisabled) {
        // Create the named game via games store, which loads it into game store
        // The store returns the sanitized game name from the backend
        const actualGameName = await this.createNewGame(this.mapName);
        
        // Navigate to the game using the sanitized name
        this.$router.push(`/game/${actualGameName}/world`);
        this.$emit("update:dialog", false);
        console.log(`Game "${actualGameName}" created!`);  
      }
    },

    closeDialog() {
      this.$emit("update:dialog", false);
      this.mapName = "";
      this.nameError = "";
    },

    updateDialog(value) {
      this.$emit("update:dialog", value);
    },

    focusInput() {
      setTimeout(() => {
        if (this.$refs.nameInput) {
          this.$refs.nameInput.focus();
        }
      }, 100);
    },
  },
  watch: {
    dialog(value) {
      if (value) {
        this.loadMaps();
        this.focusInput(); // Focus the input field when dialog opens
      }
    },
  },
};
</script>

<style scoped>
</style>
