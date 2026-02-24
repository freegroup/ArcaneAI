<template>
  <v-dialog v-model="isOpen" max-width="600px" @click:outside="close">
    <v-card class="help-dialog">
      <DialogHeader 
        :title="title" 
        @close="close" 
      />

      <v-card-text class="help-dialog-content" v-html="helpText">
      </v-card-text>

      <v-card-actions class="help-dialog-actions">
        <v-spacer></v-spacer>
        <RetroButton @click="close" variant="proceed">
          Got it!
        </RetroButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import DialogHeader from './DialogHeader.vue';
import RetroButton from './RetroButton.vue';

export default {
  name: 'ExtendedHelpDialog',
  components: { DialogHeader, RetroButton },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      required: true
    },
    helpText: {
      type: String,
      required: true
    }
  },
  computed: {
    isOpen: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    }
  },
  methods: {
    close() {
      this.isOpen = false;
    }
  }
};
</script>

<style scoped>
/* Remove rounded corners from v-dialog */
:deep(.v-overlay__content) {
  border-radius: 0 !important;
}

.help-dialog {
  background: var(--game-bg-secondary);
  color: var(--game-text-primary);
  border: 3px solid var(--game-border-highlight);
  border-radius: 0;
}

.help-dialog-content {
  padding: var(--game-spacing-xl);
  font-size: var(--game-font-size-md) !important;
  line-height: 1.6;
  color: var(--game-text-primary);
  max-height: 400px;
  overflow-y: auto;
}

/* HTML Elements in Help Text */
.help-dialog-content :deep(strong) {
  color: var(--game-accent-secondary);
  font-weight: 100;
}

.help-dialog-content :deep(code) {
  background: rgba(233, 69, 96, 0.15);
  color: #ffa07a;
  padding: 3px 4px;
  border-radius: 0;
  font-family: var(--game-font-family-mono);
  font-size: var(--game-font-size-md);
  border: 1px solid rgba(233, 69, 96, 0.3);
}

.help-dialog-content :deep(pre) {
  background: var(--game-input-bg);
  border: 1px solid var(--game-border-color);
  border-radius: 0;
  padding: var(--game-spacing-md);
  overflow-x: auto;
  margin: var(--game-spacing-sm) 0;
}

.help-dialog-content :deep(ul) {
  margin: var(--game-spacing-sm) 0;
  padding-left: var(--game-spacing-lg);
}

.help-dialog-content :deep(li) {
  margin: var(--game-spacing-xs) 0;
}

.help-dialog-actions {
  padding: var(--game-spacing-lg);
  border-top: 1px solid var(--game-border-color);
}
</style>