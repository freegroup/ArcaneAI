<template>
    <div
      :title="title"
      @click="$emit('click')"
      class="expand-btn">
      <div class="expand-btn__icon"></div>
    </div>
</template>

<script>
export default {
  name: 'ExpandButton',
  props: {
    title: {
      type: String,
      default: 'Open in fullscreen editor'
    }
  },
  emits: ['click']
}
</script>

<style scoped>
.expand-btn {
  cursor: pointer;
  position: absolute;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.expand-btn__icon {
  flex-shrink: 0;
}
</style>
