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
  justify-content: center;
}
</style>
