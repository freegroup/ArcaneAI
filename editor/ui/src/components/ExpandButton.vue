<template>
    <div 
      :title="title"
      @click="$emit('click')"
      class="icon-wrapper">
      <div class="pencil"></div>
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
.icon-wrapper {
  cursor: pointer;
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
  
  /* Container für das Icon mit Rahmen */
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  /* 4px Border in gleicher Farbe wie Hintergrund */
  background: var(--game-accent-primary, #8B4513);
  border: 4px solid var(--game-accent-primary, #8B4513);
  box-sizing: border-box;
  border-radius: 3px;
}

.icon-wrapper:hover {

  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.4);
    transform: scale(1.1);
}

.icon-wrapper .pencil {
  /* Das Icon wird im 16x16 Basis gezeichnet */
  flex-shrink: 0;
    transform: scale(1.7);
}

</style>