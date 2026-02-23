<template>
  <div class="dialog-header">
    <div class="dialog-header__content">
      <slot>
        <!-- Default: 8-bit Icon + Title -->
        <span v-if="icon" class="dialog-header__icon-8bit">{{ iconChar }}</span>
        <span v-if="title" class="dialog-header__title">{{ title }}</span>
      </slot>
    </div>
    <RetroButton 
      class="dialog-header__close" 
      size="icon" 
      variant="reset"
      @click="$emit('close')" 
      title="Close"
    >
      X
    </RetroButton>
  </div>
</template>

<script>
import RetroButton from './RetroButton.vue';

export default {
  name: 'DialogHeader',
  components: { RetroButton },
  emits: ['close'],
  props: {
    title: {
      type: String,
      default: ''
    },
    icon: {
      type: String,
      default: ''
    }
  },
  computed: {
    // Map MDI icons to 8-bit characters
    iconChar() {
      const iconMap = {
        'mdi-help-circle': '?',
        'mdi-code-braces': '{ }',
        'mdi-music-box': '♪',
        'mdi-map': '⌂',
        'mdi-gamepad-variant': '♠',
        'mdi-plus-box': '+',
        'mdi-information': 'i',
        'mdi-treasure-chest': '▣',
        'mdi-account-alert': '☺',
        'mdi-pencil': '✎'
      };
      return iconMap[this.icon] || '●';
    }
  }
};
</script>

<style scoped>
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--game-spacing-md) var(--game-spacing-lg);
  background: linear-gradient(135deg, var(--game-bg-tertiary) 0%, #1a1a2e 100%);
  border-bottom: 3px solid var(--game-accent-primary);
  min-height: 56px;
}

.dialog-header__content {
  display: flex;
  align-items: center;
  gap: var(--game-spacing-md);
  flex: 1;
}

/* 8-bit Style Icon */
.dialog-header__icon-8bit {
  font-family: var(--game-font-family-retro);
  font-size: 24px;
  color: var(--game-accent-secondary);
  text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.8),
               0 0 8px var(--game-accent-secondary);
  min-width: 32px;
  text-align: center;
}

.dialog-header__title {
  color: var(--game-accent-secondary);
  font-family: var(--game-font-family-retro);
  font-size: 16px;
  letter-spacing: 2px;
  text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.8),
               0 0 8px var(--game-accent-secondary);
}

/* 8-bit Close Button Specialized Overrides */
.dialog-header__close {
  width: 36px;
  height: 36px;
}
</style>