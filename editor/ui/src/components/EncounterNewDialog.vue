<template>
  <v-dialog v-model="dialogVisible" max-width="400" @update:model-value="onDialogChange">
    <v-card class="encounter-new-dialog">
      <DialogHeader 
        title="Create Encounter" 
        icon="mdi-sword-cross"
        @close="close" 
      />
      <v-card-text>
        <v-text-field
          ref="nameInput"
          label="Encounter Name"
          v-model="encounterName"
          :error-messages="nameError"
          @input="validateName"
          @keyup.enter="createEncounter"
        ></v-text-field>
      </v-card-text>
      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <button @click="close" class="retro-btn retro-btn--secondary retro-btn--sm">
          Cancel
        </button>
        <button 
          @click="createEncounter" 
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
import { mapActions, mapGetters, mapState } from "vuex";
import DialogHeader from './DialogHeader.vue';

export default {
  name: 'EncounterNewDialog',
  components: { DialogHeader },
  
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  
  emits: ['update:modelValue'],
  
  data() {
    return {
      encounterName: "",
      nameError: "",
    };
  },
  
  computed: {
    ...mapGetters("views", ["encounterViews"]),
    ...mapState("game", ["gameName"]),
    
    dialogVisible: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    },
    
    existingNames() {
      return this.encounterViews.map(v => v.encounterConfig?.name?.toLowerCase() || '');
    },
    
    isCreateDisabled() {
      return !this.encounterName.trim() || this.nameError !== "";
    },
  },
  
  watch: {
    modelValue(newVal) {
      if (newVal) {
        // Dialog opened - reset state and focus input
        this.encounterName = '';
        this.nameError = '';
        this.focusInput();
      }
    }
  },
  
  methods: {
    ...mapActions("views", ["createEncounterView"]),
    ...mapActions("encounters", ["fetchEncounters"]),

    validateName() {
      const trimmedName = this.encounterName.trim().toLowerCase();
      if (this.existingNames.includes(trimmedName)) {
        this.nameError = "An encounter with this name already exists.";
      } else {
        this.nameError = "";
      }
    },

    /**
     * Create new encounter - all business logic self-contained.
     * 1. Creates encounter view in store (which also saves to server)
     * 2. Refreshes encounters list for navigation sidebar
     * 3. Navigates to the new encounter
     */
    async createEncounter() {
      if (this.isCreateDisabled) return;
      
      const name = this.encounterName.trim();
      
      console.log(`[EncounterNewDialog] Creating encounter "${name}" for game: ${this.gameName}`);
      
      try {
        // Step 1: Create encounter view in store (saves to server)
        // Pass gameName explicitly to ensure it's available
        const viewId = await this.createEncounterView({ 
          encounterName: name, 
          gameName: this.gameName 
        });
        console.log(`[EncounterNewDialog] Encounter "${name}" created with viewId: ${viewId}`);
        
        // Step 2: Refresh encounters list for navigation sidebar
        await this.fetchEncounters(this.gameName);
        console.log(`[EncounterNewDialog] Encounters list refreshed`);
        
        // Step 3: Navigate to the new encounter
        const encounterId = viewId.replace('encounter_', '');
        this.$router.push(`/game/${this.gameName}/encounter/${encounterId}`);
        
        // Step 4: Close dialog
        this.close();
      } catch (error) {
        console.error(`[EncounterNewDialog] Failed to create encounter:`, error);
        // Show error to user (could add a snackbar/toast here)
        this.nameError = `Failed to create encounter: ${error.message}`;
      }
    },

    close() {
      this.dialogVisible = false;
    },

    onDialogChange(value) {
      if (!value) {
        // Reset when dialog closes
        this.encounterName = '';
        this.nameError = '';
      }
    },

    focusInput() {
      this.$nextTick(() => {
        if (this.$refs.nameInput) {
          this.$refs.nameInput.focus();
        }
      });
    },
  },
};
</script>

<style scoped>
.encounter-new-dialog {
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