<template>
  <button
    type="button"
    :class="[
      'retro-btn',
      variant ? `retro-btn--${variant}` : ''
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
  name: 'RetroButton',
  props: {
    variant: {
      type: String,
      default: '' // proceed, reset, secondary, disabled
    }
  },
  emits: ['click']
};
</script>

<style>
.retro-btn {
  --btn-bg: var(--game-success);
  --btn-bg-hover: #229954;
  --btn-shadow: #1e8449;
  --btn-outline: 4px;
  --btn-shadow-width: 3px;

  background: var(--btn-bg);
  display: inline-block;
  position: relative;
  text-align: center;
  font-size: var(--game-font-size-sm);
  padding: 6px 16px;
  letter-spacing: 2px;
  text-decoration: none;
  color: #ffffff;
  border: none;
  border-radius: 0;
  cursor: pointer;
  box-shadow: inset calc(var(--btn-shadow-width) * -1) calc(var(--btn-shadow-width) * -1) 0px 0px var(--btn-shadow);
  transition: all var(--game-transition-fast);
  
  /* Reset button defaults to ensure consistent rendering */
  font-family: var(--game-font-family-retro);
  line-height: 1;
  margin: 0;
  box-sizing: border-box;
}

.retro-btn:hover,
.retro-btn:focus {
  background: var(--btn-bg-hover);
  box-shadow: inset calc(var(--btn-shadow-width) * -1.5) calc(var(--btn-shadow-width) * -1.5) 0px 0px var(--btn-shadow);
  outline: none;
}

.retro-btn:active {
  box-shadow: inset var(--btn-shadow-width) var(--btn-shadow-width) 0px 0px var(--btn-shadow);
}

/* Pixel border effect using pseudo-elements */
.retro-btn::before,
.retro-btn::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  box-sizing: content-box;
  pointer-events: none;
}

.retro-btn::before {
  top: calc(var(--btn-outline) * -1);
  left: 0;
  border-top: var(--btn-outline) black solid;
  border-bottom: var(--btn-outline) black solid;
}

.retro-btn::after {
  left: calc(var(--btn-outline) * -1);
  top: 0;
  border-left: var(--btn-outline) black solid;
  border-right: var(--btn-outline) black solid;
}

/* Golden/Proceed variant */
.retro-btn--proceed {
  --btn-bg: var(--game-accent-secondary);
  --btn-bg-hover: #e67e22;
  --btn-shadow: #d35400;
  color: #1a1a2e !important;
}

/* Red/Reset/Danger variant */
.retro-btn--reset {
  --btn-bg: var(--game-accent-primary);
  --btn-bg-hover: #d32f2f;
  --btn-shadow: #b71c1c;
  color: #ffffff !important;
}

/* Secondary/Dark variant */
.retro-btn--secondary {
  --btn-bg: var(--game-bg-tertiary);
  --btn-bg-hover: var(--game-bg-secondary);
  --btn-shadow: #0a0a14;
  color: white !important;
}

/* Disabled state */
.retro-btn:disabled,
.retro-btn--disabled {
  --btn-bg: #666;
  --btn-bg-hover: #666;
  --btn-shadow: #444;
  cursor: not-allowed;
  opacity: 0.6;
}

</style>
