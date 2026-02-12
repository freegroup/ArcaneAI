<template>
  <v-dialog :model-value="dialog" max-width="400" @click:outside="closeDialog" @update:model-value="updateDialog">
    <v-card class="file-new-dialog">
      <DialogHeader 
        title="Create Map" 
        icon="mdi-plus-box"
        @close="closeDialog" 
      />
      <v-card-text>
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
        <button @click="closeDialog" class="retro-btn retro-btn--secondary retro-btn--sm">
          Cancel
        </button>
        <button 
          @click="createDialog" 
          :disabled="isCreateDisabled" 
          class="retro-btn retro-btn--sm"
          :class="{ 'retro-btn--disabled': isCreateDisabled }"
        >
          Create
        </button>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapActions, mapGetters } from "vuex";
import DialogHeader from './DialogHeader.vue';

export default {
  components: { DialogHeader },
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
    ...mapGetters("maps", ["maps"]),
    isCreateDisabled() {
      return !this.mapName || this.maps.includes(this.mapName);
    },
  },
  methods: {
    ...mapActions("maps", ["fetchMaps", "createNewMap"]),

    async loadMaps() {
      await this.fetchMaps();
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
        // Create the named map content and store it in Vuex
        await this.createNewMap(this.mapName);
        this.$router.replace({ name: this.$route.name, params: { mapName: this.mapName } });
        this.$emit("update:dialog", false);
        console.log(`Map "${this.mapName}" created!`);  
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
      // Set focus on the input field when dialog opens
      this.$nextTick(() => {
        if (this.$refs.nameInput) {
          this.$refs.nameInput.focus();
        }
      });
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
.file-new-dialog {
  background: var(--game-bg-secondary) !important;
  color: var(--game-text-primary) !important;
  border: 2px solid var(--game-border-highlight);
  border-radius: 0;
}

.dialog-actions {
  padding: var(--game-spacing-lg);
  border-top: 1px solid var(--game-border-color);
  background: var(--game-bg-tertiary);
  gap: var(--game-spacing-md);
}
</style>
