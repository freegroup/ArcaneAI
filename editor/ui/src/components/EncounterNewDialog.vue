<template>
  <v-dialog v-model="dialogVisible" max-width="600" @update:model-value="onDialogChange">
    <v-card class="encounter-new-dialog">
      <DialogHeader
        title="Create Encounter"
        @close="close"
      />
      <v-card-text class="dialog-content">
        <p class="dialog-description">
          An Encounter is a <span class="desc-accent">focused view</span> of your game —
          a lens that reveals only the rooms and connections relevant to
          a specific <span class="desc-accent">scenario</span>.
          Build and refine one piece of the puzzle at a time.
          Every connection or room you create here is automatically part of the <span class="desc-accent">World</span> map.
        </p>
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
        <ThemedButton @click="close" variant="secondary">
          Cancel
        </ThemedButton>
        <ThemedButton 
          @click="createEncounter" 
          :disabled="isCreateDisabled" 
        >
          Create
        </ThemedButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapActions, mapGetters, mapState } from "vuex";
import DialogHeader from './DialogHeader.vue';
import ThemedButton from './ThemedButton.vue';

export default {
  name: 'EncounterNewDialog',
  components: { DialogHeader, ThemedButton },
  
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    initialName: {
      type: String,
      default: ''
    }
  },
  
  emits: ['update:modelValue', 'created'],
  
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
        // Dialog opened - set initial name (or reset) and focus input
        this.encounterName = this.initialName || '';
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
        
        // Step 3: Emit created event with viewId
        this.$emit('created', viewId);
        
        // Step 4: Navigate to the new encounter
        const encounterId = viewId.replace('encounter_', '');
        this.$router.push(`/game/${this.gameName}/encounter/${encounterId}`);
        
        // Step 5: Close dialog
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
      setTimeout(() => {
        if (this.$refs.nameInput) {
          this.$refs.nameInput.focus();
        }
      }, 100);
    },
  },
};
</script>

<style scoped>
</style>