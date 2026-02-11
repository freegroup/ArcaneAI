<template>
  <v-dialog v-model="isOpen" max-width="600px" @click:outside="close">
    <v-card class="help-dialog">
      <v-card-title class="help-dialog-title">
        <v-icon class="help-icon">mdi-help-circle</v-icon>
        {{ title }}
        <v-spacer></v-spacer>
        <v-btn icon size="small" @click="close">
          <v-icon>mdi-close</v-icon>
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
.help-dialog {
  background: var(--game-bg-secondary);
  color: var(--game-text-primary);
  border: 2px solid var(--game-border-highlight);
  border-radius: var(--game-radius-lg);
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

.help-dialog-title :deep(.v-btn) {
  background: transparent;
  color: var(--game-text-secondary);
}

.help-dialog-title :deep(.v-btn:hover) {
  background: var(--game-input-hover);
  color: var(--game-text-primary);
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
  border-radius: 4px;
  font-family: var(--game-font-family-mono);
  font-size: 14px;
  border: 1px solid rgba(233, 69, 96, 0.3);
  font-weight: 500;
}

.help-dialog-content :deep(pre) {
  background: var(--game-input-bg);
  border: 1px solid var(--game-border-color);
  border-radius: var(--game-radius-md);
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
  background: var(--game-accent-primary);
  color: var(--game-text-primary);
  font-weight: 600;
  padding: var(--game-spacing-sm) var(--game-spacing-xl);
  border-radius: var(--game-radius-md);
  transition: all var(--game-transition-fast);
}

.close-btn:hover {
  background: var(--game-accent-tertiary);
  box-shadow: var(--game-shadow-glow);
  transform: translateY(-2px);
}
</style>