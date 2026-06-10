<template>
  <div class="rooms-empty">
    <div class="rooms-empty__inner">
      <v-icon icon="mdi-door" size="64" class="rooms-empty__icon" />
      <h2 class="rooms-empty__title">Rooms</h2>
      <p class="rooms-empty__text">
        Select a room from the sidebar to see its details.
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RoomsEmptyState',
  props: {
    gameName: { type: String, default: '' }
  }
}
</script>

<style scoped>
.rooms-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
}
.rooms-empty__inner {
  text-align: center;
  opacity: 0.6;
}
.rooms-empty__icon {
  margin-bottom: 16px;
}
.rooms-empty__title {
  margin: 0 0 8px 0;
  font-weight: 600;
}
.rooms-empty__text {
  margin: 0;
  font-size: 0.95rem;
}
</style>
