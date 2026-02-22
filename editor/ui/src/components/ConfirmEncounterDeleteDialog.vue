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
        <button @click="cancel" class="retro-btn retro-btn--secondary retro-btn--sm">
          Cancel
        </button>
        <button 
          @click="confirmDelete" 
          class="retro-btn retro-btn--danger retro-btn--sm"
        >
          Delete
        </button>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import DialogHeader from './DialogHeader.vue';

export default {
  name: 'ConfirmEncounterDeleteDialog',
  components: { DialogHeader },
  
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

.dialog-actions .retro-btn {
  margin-left: var(--game-spacing-md);
}

/* Retro Button Styles */
.retro-btn {
  font-family: var(--game-font-family-retro);
  font-size: 12px;
  letter-spacing: 1px;
  padding: var(--game-spacing-sm) var(--game-spacing-lg);
  border: none;
  cursor: pointer;
  transition: all var(--game-transition-fast);
}

.retro-btn--sm {
  padding: var(--game-spacing-xs) var(--game-spacing-md);
  font-size: 11px;
}

.retro-btn--danger {
  background: var(--game-accent-primary);
  color: white;
  box-shadow: inset -3px -3px 0px 0px #8c2022;
}

.retro-btn--danger:hover {
  background: #ce372b;
  box-shadow: inset -4px -4px 0px 0px #8c2022;
}

.retro-btn--danger:active {
  box-shadow: inset 3px 3px 0px 0px #8c2022;
}

.retro-btn--secondary {
  background: var(--game-bg-tertiary);
  color: var(--game-text-secondary);
  border: 2px solid var(--game-border-color);
}

.retro-btn--secondary:hover {
  border-color: var(--game-accent-primary);
  color: var(--game-accent-secondary);
}
</style>