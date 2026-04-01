<template>
  <div class="empty-state">
    <div class="empty-state__container">
      <div class="empty-state__icon">
        <img src="@/assets/logo.png" class="empty-state__logo" alt="ArcaneAI Logo" />
      </div>

      <h2 class="empty-state__title">Willkommen im Studio</h2>

      <p class="empty-state__subtitle">
        Erschaffe dein eigenes Text Adventure.
      </p>

      <div class="empty-state__actions">
        <ThemedButton @click="$emit('new-game')" variant="proceed">Neues Abenteuer designen</ThemedButton>
        <ThemedButton @click="$emit('load-game')" variant="secondary">Abenteuer weitergestalten</ThemedButton>
      </div>
    </div>
  </div>
</template>

<script>
import ThemedButton from './ThemedButton.vue';

export default {
  name: 'ArcaneAIEmptyState',
  components: { ThemedButton },
  props: {
  },
  emits: ['new-game', 'load-game'],
}
</script>

<style scoped>
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}

.empty-state__container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.empty-state__icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state__subtitle {
  text-align: center;
}

.empty-state__actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.empty-state__logo {
  width: 160px;
  height: 160px;
  object-fit: contain;
  animation: float 6s infinite ease-in-out;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

</style>
