<template>
  <div class="dialog-header">
    <div class="dialog-header__content">
      <slot>
        <!-- Default: 8-bit Icon + Title -->
        <span v-if="icon" class="dialog-header__icon-8bit">{{ iconChar }}</span>
        <span v-if="title" class="dialog-header__title">{{ title }}</span>
      </slot>
    </div>
    <button class="dialog-header__close" @click="$emit('close')" title="Close">
      X
    </button>
  </div>
</template>

<script>
export default {
  name: 'DialogHeader',
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
        'mdi-account-alert': '☺'
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

/* 8-bit Close Button */
.dialog-header__close {
  background: var(--game-accent-primary);
  color: white;
  border: none;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-family: var(--game-font-family-retro);
  font-size: 14px;
  font-weight: bold;
  transition: all var(--game-transition-fast);
  position: relative;
  box-shadow: inset -4px -4px 0px 0px #8c2022;
}

.dialog-header__close::before {
  content: '';
  position: absolute;
  top: -3px;
  left: 0;
  width: 100%;
  height: 100%;
  border-top: 3px solid black;
  border-bottom: 3px solid black;
  box-sizing: content-box;
  pointer-events: none;
}

.dialog-header__close::after {
  content: '';
  position: absolute;
  left: -3px;
  top: 0;
  width: 100%;
  height: 100%;
  border-left: 3px solid black;
  border-right: 3px solid black;
  box-sizing: content-box;
  pointer-events: none;
}

.dialog-header__close:hover {
  background: #ce372b;
  box-shadow: inset -6px -6px 0px 0px #8c2022;
}

.dialog-header__close:active {
  box-shadow: inset 4px 4px 0px 0px #8c2022;
}
</style>