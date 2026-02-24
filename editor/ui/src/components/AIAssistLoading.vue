<template>
  <div class="ai-assist-loading">
    <v-progress-circular 
      indeterminate 
      color="primary" 
      size="20" 
      width="2"
      class="ai-assist-loading__spinner"
    ></v-progress-circular>
    <span class="ai-assist-loading__text">
      <slot>AI is working...</slot>
    </span>
  </div>
</template>

<script>
export default {
  name: 'AIAssistLoading'
};
</script>

<style scoped>
.ai-assist-loading {
  display: flex;
  align-items: center;
  gap: var(--game-spacing-md);
  justify-content: center;
  padding: var(--game-spacing-lg);
  color: var(--game-text-secondary);
  font-family: var(--game-font-family-retro);
  font-size: 14px;
}

.ai-assist-loading__spinner {
  filter: drop-shadow(0 0 5px var(--game-accent-primary));
}

.ai-assist-loading__text {
  letter-spacing: 1px;
}
</style>
