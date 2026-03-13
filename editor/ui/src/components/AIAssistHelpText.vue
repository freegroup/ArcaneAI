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
}

.ai-assist-help__icon {
  flex-shrink: 0;
}

.ai-assist-help__list {
  list-style: none;
}

.ai-assist-help__list li {
  position: relative;
}

.ai-assist-help__list li::before {
  content: '-';
  position: absolute;
  left: 0;
}
</style>
