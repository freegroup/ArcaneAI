<template>
  <span class="help-btn" @click="$emit('click')">?</span>
</template>

<script>
export default {
  name: 'HelpButton',
  emits: ['click']
};
</script>

<style scoped>
.help-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  line-height: 1;
  user-select: none;
}
</style>
