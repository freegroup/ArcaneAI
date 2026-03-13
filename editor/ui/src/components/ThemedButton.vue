<template>
  <button
    type="button"
    :class="[
      'themed-btn',
      variant ? `themed-btn--${variant}` : ''
    ]"
    @click.stop="$emit('click', $event)"
    @mousedown.stop
    @pointerdown.stop
    @mouseup.stop
  >
    <slot></slot>
  </button>
</template>

<script>
export default {
  name: 'ThemedButton',
  props: {
    variant: {
      type: String,
      default: '' // proceed, reset, secondary, disabled
    }
  },
  emits: ['click']
};
</script>

<style scoped>
.themed-btn {
  display: inline-block;
  position: relative;
  text-align: center;
  text-decoration: none;
  cursor: pointer;
  line-height: 1;
  margin: 0;
  box-sizing: border-box;
}

.themed-btn::before,
.themed-btn::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  box-sizing: content-box;
  pointer-events: none;
}
</style>
