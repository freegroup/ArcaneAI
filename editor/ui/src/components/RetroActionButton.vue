<template>
  <button
    type="button"
    :class="[
      'retro-action-btn',
      variant ? `retro-action-btn--${variant}` : ''
    ]"
    @click.stop="$emit('click', $event)"
    :title="title"
  >
    <slot></slot>
  </button>
</template>

<script>
export default {
  name: 'RetroActionButton',
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
.retro-action-btn {
  --action-btn-size: 20px;
  --action-btn-bg: var(--game-success);
  --action-btn-shadow: #1e8449;
  --action-btn-outline: 2px;
  
  width: var(--action-btn-size);
  height: var(--action-btn-size);
  min-width: var(--action-btn-size);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: var(--action-btn-bg);
  border: none;
  cursor: pointer;
  box-shadow: inset -3px -3px 0px 0px var(--action-btn-shadow);
  color: #ffffff;
  font-family: var(--game-font-family-retro);
  font-size: 20px;
  line-height: 1;
  padding: 0;
  transition: all var(--game-transition-fast);
  margin: 2px;
  box-sizing: border-box;
}

.retro-action-btn:hover {
  filter: brightness(1.1);
  box-shadow: inset -4px -4px 0px 0px var(--action-btn-shadow);
}

.retro-action-btn:active {
  box-shadow: inset 3px 3px 0px 0px var(--action-btn-shadow);
  transform: translateY(1px);
}

/* 8-bit border */
.retro-action-btn::before {
  content: '';
  position: absolute;
  top: calc(var(--action-btn-outline) * -1);
  left: 0;
  right: 0;
  bottom: calc(var(--action-btn-outline) * -1);
  border-top: var(--action-btn-outline) solid black;
  border-bottom: var(--action-btn-outline) solid black;
  pointer-events: none;
  box-sizing: content-box;
}

.retro-action-btn::after {
  content: '';
  position: absolute;
  left: calc(var(--action-btn-outline) * -1);
  top: 0;
  right: calc(var(--action-btn-outline) * -1);
  bottom: 0;
  border-left: var(--action-btn-outline) solid black;
  border-right: var(--action-btn-outline) solid black;
  pointer-events: none;
  box-sizing: content-box;
}

/* Success/Add variant */
.retro-action-btn--success {
  --action-btn-bg: var(--game-success);
  --action-btn-shadow: #1e8449;
}

/* Danger/Delete variant */
.retro-action-btn--danger {
  --action-btn-bg: var(--game-accent-primary);
  --action-btn-shadow: #b71c1c;
}

/* Secondary/Edit variant */
.retro-action-btn--secondary {
  --action-btn-bg: var(--game-bg-tertiary);
  --action-btn-shadow: #0a0a14;
}

/* Disabled state */
.retro-action-btn:disabled {
  --action-btn-bg: #666;
  --action-btn-shadow: #444;
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
