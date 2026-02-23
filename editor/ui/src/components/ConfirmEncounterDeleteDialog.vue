<template>
  <v-dialog :model-value="modelValue" max-width="500" @click:outside="cancel" @update:model-value="updateDialog">
    <v-card class="delete-encounter-dialog">
      <DialogHeader 
        title="Remove Encounter" 
        icon="mdi-map-marker"
        @close="cancel" 
      />
      <v-card-text class="dialog-content">
        <p class="confirm-text">
          Remove encounter <strong>"{{ encounterName }}"</strong>?
        </p>
      </v-card-text>
      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <RetroButton @click="cancel" variant="secondary" size="sm">
          Cancel
        </RetroButton>
        <RetroButton 
          @click="confirmDelete" 
          variant="reset" 
          size="sm"
        >
          Delete
        </RetroButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import DialogHeader from './DialogHeader.vue';
import RetroButton from './RetroButton.vue';

export default {
  name: 'ConfirmEncounterDeleteDialog',
  components: { DialogHeader, RetroButton },
  
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    encounterId: {
      type: String,
      default: ''
    },
    encounterName: {
      type: String,
      default: ''
    }
  },
  
  emits: ['update:modelValue', 'confirm'],
  
  methods: {
    confirmDelete() {
      this.$emit('confirm', this.encounterId)
      this.$emit('update:modelValue', false)
    },
    
    cancel() {
      this.$emit('update:modelValue', false)
    },
    
    updateDialog(value) {
      this.$emit('update:modelValue', value)
    }
  }
}
</script>

<style scoped>
.delete-encounter-dialog {
  background: var(--game-bg-secondary);
  color: var(--game-text-primary);
  border: 2px solid var(--game-accent-primary);
  border-radius: var(--game-radius-lg);
  box-shadow: var(--game-shadow-lg);
}

.dialog-content {
  padding: var(--game-spacing-xl, 32px) var(--game-spacing-lg);
  background: var(--game-bg-secondary);
  min-height: 80px;
}

.confirm-text {
  font-family: var(--game-font-family-retro);
  font-size: var(--game-font-size-md);
  color: var(--game-text-primary);
  text-align: center;
  margin: var(--game-spacing-md) 0;
  line-height: 1.6;
}

.confirm-text strong {
  color: var(--game-accent-secondary);
}

.dialog-actions {
  padding: var(--game-spacing-lg) var(--game-spacing-lg);
  border-top: 1px solid var(--game-border-color);
  background: var(--game-bg-tertiary);
}

.dialog-actions > :deep(.retro-btn) {
  margin-left: var(--game-spacing-md);
}
</style>