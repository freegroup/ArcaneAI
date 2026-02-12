<template>
  <span class="help-btn-8bit" @click="$emit('click')">?</span>
</template>

<script>
export default {
  name: 'HelpButton',
  emits: ['click']
};
</script>

<style scoped>
/* 8-bit Style Help Button */
.help-btn-8bit {
  font-family: var(--game-font-family-retro);
  font-size: 12px;
  color: var(--game-text-muted);
  background: var(--game-bg-secondary);
  border: 2px solid var(--game-border-color);
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--game-transition-fast);
  line-height: 1;
  user-select: none;
}

.help-btn-8bit:hover {
  color: var(--game-accent-secondary);
  border-color: var(--game-accent-secondary);
  background: var(--game-input-hover);
  transform: scale(1.1);
}
</style>