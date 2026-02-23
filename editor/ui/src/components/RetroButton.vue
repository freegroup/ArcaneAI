<template>
  <button
    :class="[
      'retro-btn',
      variant ? `retro-btn--${variant}` : '',
      size ? `retro-btn--${size}` : ''
    ]"
    @click="$emit('click', $event)"
  >
    <slot></slot>
  </button>
</template>

<script>
export default {
  name: 'RetroButton',
  props: {
    variant: {
      type: String,
      default: '' // proceed, reset, secondary, disabled
    },
    size: {
      type: String,
      default: '' // sm, lg, icon
    }
  },
  emits: ['click']
};
</script>

<style scoped>
/* Redundant logic from game-theme.css but localized for component safety if needed, 
   though game-theme.css is global. Keeping it clean by just using the classes. */
</style>
