<template>
  <div class="empty-state">
    <div class="empty-state__container">
      <div class="empty-state__icon">
        <span class="pixel-scroller">?</span>
      </div>
      
      <h2 class="empty-state__title">...LOAD TO START</h2>
      
      <div class="empty-state__content">
        <p class="empty-state__text highlight">
          HEAR YE, BRAVE ARCHITECT OF INTERACTIVE FICTION!
        </p>
        
        <p class="empty-state__text">
          You are currently wandering through a digital void. ArcaneAI has detected a severe lack of adventures.
        </p>
        
        <div class="empty-state__description">
          <p>
            <span class="accent-text">ArcaneAI</span> is the mystical bridge between two worlds:
          </p>
          <ul class="empty-state__list">
            <li>The clunky, pixelated charm of 80s text adventures (where "GO NORTH" was the height of technology).</li>
            <li>The dynamic, slightly sarcastic intelligence of modern LLMs (where your NPCs might actually have existential crises).</li>
          </ul>
          <p>
            We help you combine the golden era of "Blank Screen, Flashing Cursor" with the narrative power of today's neural networks. 
            It's like giving your old C64 a college degree and a questionable sense of humor.
          </p>
        </div>
        
        <div class="empty-state__call-to-action">
          <v-icon class="swing">mdi-arrow-up</v-icon>
          <p>Use the buttons in the sky above to summon a <strong>New Game</strong> or <strong>Load</strong> an existing archive. The dragons are getting impatient.</p>
        </div>
      </div>
      
      <div class="empty-state__footer">
        <span class="pixel-art-cat">(=^·ω·^=)</span>
        <span class="status-msg">System Idle... Waiting for Imagination...</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ArcaneAIEmptyState'
}
</script>

<style scoped>
.empty-state {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  min-height: 100%;
  overflow-y: auto;
}

.empty-state__container {
  position: relative;
}

.empty-state__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.empty-state__icon::before {
  content: '';
  position: absolute;
  top: -4px;
  left: 0;
  box-sizing: content-box;
}

.empty-state__icon::after {
  content: '';
  position: absolute;
  left: -4px;
  top: 0;
  box-sizing: content-box;
}

.empty-state__text {
  text-align: center;
}

.empty-state__list {
  list-style: none;
}

.empty-state__list li {
  position: relative;
}

.empty-state__list li::before {
  content: '>';
  position: absolute;
  left: 0;
}

.empty-state__call-to-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.swing {
  animation: swing 2s infinite ease-in-out;
}

@keyframes swing {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-15px); }
}

.pixel-scroller {
  animation: bounce 2s infinite ease-in-out;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.empty-state__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
