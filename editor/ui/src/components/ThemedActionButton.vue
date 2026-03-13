<template>
  <button
    type="button"
    :class="[
      'themed-action-btn',
      variant ? `themed-action-btn--${variant}` : ''
    ]"
    @click.stop="$emit('click', $event)"
    :title="title"
  >
    <slot></slot>
  </button>
</template>

<script>
export default {
  name: 'ThemedActionButton',
  props: {
    variant: {
      type: String,
      default: '' // success, danger, secondary
    },
    title: {
      type: String,
      default: ''
    }
  },
  emits: ['click']
};
</script>

<style scoped>
.themed-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  box-sizing: border-box;
}

.themed-action-btn::before,
.themed-action-btn::after {
  content: '';
  position: absolute;
  pointer-events: none;
  box-sizing: content-box;
}

.themed-action-btn::before {
  left: 0;
  right: 0;
}

.themed-action-btn::after {
  top: 0;
  bottom: 0;
}
</style>
