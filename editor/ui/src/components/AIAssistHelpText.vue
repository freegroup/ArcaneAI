<template>
  <div class="ai-assist-help">
    <div class="ai-assist-help__content">
      <div class="ai-assist-help__title">How does AI Assist work?</div>
      <p class="ai-assist-help__description">Give the AI an instruction on how to improve your text:</p>
      <ul class="ai-assist-help__list">
        <li>"Make it more mysterious and atmospheric"</li>
        <li>"Add sensory details (sounds, smells, etc.)"</li>
        <li>"Make it shorter and punchier"</li>
        <li>"Translate to German"</li>
      </ul>
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AIAssistHelpText'
};
</script>

<style scoped>
.ai-assist-help {
  display: flex;
  gap: var(--game-spacing-md);
  color: white;
}

.ai-assist-help__icon {
  flex-shrink: 0;
}

.ai-assist-help__title {
  color: white;
  margin-bottom: var(--game-spacing-sm);
  font-size: var(--game-font-size-md);
  letter-spacing: 4px;
}

.ai-assist-help__description {
  margin: var(--game-spacing-sm) 0;
  font-size: var(--game-font-size-sm);
  letter-spacing: 4px;
}

.ai-assist-help__list {
  margin: var(--game-spacing-sm) 0;
  padding-left: 20px;
  list-style: none;
  letter-spacing: 4px;
}

.ai-assist-help__list li {
  margin: 8px 0;
  font-size: var(--game-font-size-sm);
  position: relative;
  padding-left: 15px;
  letter-spacing: 4px;
}

.ai-assist-help__list li::before {
  content: '-';
  position: absolute;
  left: 0;
  color: var(--game-accent-secondary);
}
</style>
