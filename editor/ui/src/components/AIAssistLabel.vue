<template>
  <span class="ai-assist-label">
    <v-icon size="small" color="primary" class="ai-assist-label__icon">mdi-robot</v-icon>
    <span class="ai-assist-label__text">
      <slot>AI ASSIST</slot>
    </span>
  </span>
</template>

<script>
export default {
  name: 'AIAssistLabel'
};
</script>

<style scoped>
.ai-assist-label {
  display: flex;
  align-items: center;
}
</style>
