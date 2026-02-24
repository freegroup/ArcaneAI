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
  font-size: 24px;
  color: var(--game-text-muted);
  background: var(--game-bg-secondary);
  border: 2px solid var(--game-border-color);
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--game-transition-fast);
  line-height: 1;
  user-select: none;
}

.help-btn-8bit:hover {
  color: var(--game-success);;
  border-color: var(--game-success);;
  background: var(--game-input-hover);
}
</style>