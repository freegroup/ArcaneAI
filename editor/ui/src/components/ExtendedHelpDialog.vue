<template>
  <v-dialog v-model="isOpen" max-width="600px" @click:outside="close">
    <v-card class="help-dialog">
      <v-card-title class="help-dialog-title">
        <v-icon class="help-icon">mdi-help-circle</v-icon>
        {{ title }}
        <v-spacer></v-spacer>
        <v-btn icon size="small" @click="close" class="close-icon-btn">
          X
        </v-btn>
      </v-card-title>

      <v-card-text class="help-dialog-content" v-html="helpText">
      </v-card-text>

      <v-card-actions class="help-dialog-actions">
        <v-spacer></v-spacer>
        <v-btn @click="close" class="close-btn">
          Got it!
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'ExtendedHelpDialog',
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

.help-dialog-title {
  background: var(--game-bg-tertiary);
  color: var(--game-accent-secondary);
  font-size: var(--game-font-size-lg);
  font-weight: 600;
  padding: var(--game-spacing-lg);
  border-bottom: 1px solid var(--game-border-color);
  display: flex;
  align-items: center;
  gap: var(--game-spacing-sm);
}

.help-icon {
  color: var(--game-accent-secondary);
  font-size: 28px;
}

.close-icon-btn {
  background: transparent !important;
  color: var(--game-text-secondary) !important;
  font-family: var(--game-font-family-retro) !important;
  font-size: 16px !important;
  min-width: 32px !important;
  height: 32px !important;
  border-radius: 0 !important;
}

.close-icon-btn:hover {
  background: var(--game-input-hover) !important;
  color: var(--game-text-primary) !important;
}

.help-dialog-content {
  padding: var(--game-spacing-xl);
  font-size: var(--game-font-size-md);
  line-height: 1.6;
  color: var(--game-text-primary);
  max-height: 400px;
  overflow-y: auto;
}

/* HTML Elements in Help Text */
.help-dialog-content :deep(strong) {
  color: var(--game-accent-secondary);
  font-weight: 700;
}

.help-dialog-content :deep(code) {
  background: rgba(233, 69, 96, 0.15);
  color: #ffa07a;
  padding: 3px 8px;
  border-radius: 0;
  font-family: var(--game-font-family-mono);
  font-size: 14px;
  border: 1px solid rgba(233, 69, 96, 0.3);
  font-weight: 500;
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

.close-btn {
  background: var(--game-accent-primary) !important;
  color: var(--game-text-primary) !important;
  font-family: var(--game-font-family-retro) !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
  padding: 12px 24px !important;
  border-radius: 0 !important;
  box-shadow: inset -4px -4px 0px 0px #8c2022,
              0 0 0 3px black !important;
  transition: all var(--game-transition-fast) !important;
}

.close-btn:hover {
  background: var(--game-accent-tertiary) !important;
  box-shadow: inset -6px -6px 0px 0px #8c2022,
              0 0 0 3px black !important;
}

.close-btn:active {
  box-shadow: inset 4px 4px 0px 0px #8c2022,
              0 0 0 3px black !important;
}
</style>