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
  align-items: flex-start;  /* Changed from center - prevents top clipping */
  justify-content: center;
  min-height: 100%;
  width: 100%;
  background: radial-gradient(circle at center, var(--game-bg-secondary) 0%, var(--game-bg-primary) 100%);
  padding: var(--game-spacing-lg);
  overflow-y: auto;
}

.empty-state__container {
  max-width: 700px;  /* Slightly smaller for better fit */
  width: 100%;
  background: rgba(15, 52, 96, 0.4);
  border: 3px solid var(--game-accent-primary);
  padding: var(--game-spacing-lg);  /* Reduced padding */
  margin: auto 0;  /* Center vertically when space available */
  position: relative;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(233, 69, 96, 0.1);
}

/* Pixel Art Inspired Icon */
.empty-state__icon {
  width: 80px;
  height: 80px;
  background: var(--game-accent-primary);
  margin: 0 auto var(--game-spacing-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: 6px 6px 0px 0px rgba(0, 0, 0, 0.5);
}

.empty-state__icon::before {
  content: '';
  position: absolute;
  top: -4px;
  left: 0;
  width: 100%;
  height: 100%;
  border-top: 4px solid black;
  border-bottom: 4px solid black;
  box-sizing: content-box;
}

.empty-state__icon::after {
  content: '';
  position: absolute;
  left: -4px;
  top: 0;
  width: 100%;
  height: 100%;
  border-left: 4px solid black;
  border-right: 4px solid black;
  box-sizing: content-box;
}

.pixel-scroller {
  font-family: var(--game-font-family-retro);
  font-size: 48px;
  color: white;
  animation: bounce 2s infinite ease-in-out;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.empty-state__title {
  font-family: var(--game-font-family-retro);
  font-size: 32px;
  text-align: center;
  color: var(--game-accent-secondary);
  margin-bottom: var(--game-spacing-xl);
  text-transform: uppercase;
  letter-spacing: 3px;
}

.empty-state__content {
  font-family: var(--game-font-family-retro);
  font-size: 16px;
  line-height: 1.8;
  color: var(--game-text-primary);
}

.empty-state__text {
  margin-bottom: var(--game-spacing-md);
  text-align: center;
}

.empty-state__text.highlight {
  color: var(--game-accent-secondary);
  font-size: 18px;
  margin-bottom: var(--game-spacing-lg);
}

.empty-state__description {
  background: rgba(0, 0, 0, 0.3);
  padding: var(--game-spacing-md);  /* Reduced from lg */
  border-left: 4px solid var(--game-accent-secondary);
  margin-bottom: var(--game-spacing-lg);  /* Reduced from xl */
}

.accent-text {
  color: var(--game-accent-primary);
}

.empty-state__list {
  list-style: none;
  padding: 0;
  margin: var(--game-spacing-md) 0;
}

.empty-state__list li {
  margin-bottom: var(--game-spacing-sm);
  padding-left: 24px;
  position: relative;
  font-size: 14px;
}

.empty-state__list li::before {
  content: '>';
  position: absolute;
  left: 0;
  color: var(--game-accent-secondary);
}

.empty-state__call-to-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--game-spacing-sm);  /* Reduced from md */
  margin-top: var(--game-spacing-lg);  /* Reduced from xl */
  padding: var(--game-spacing-sm);  /* Reduced from md */
  border: 1px dashed var(--game-text-muted);
  text-align: center;
  color: var(--game-text-secondary);
}

.empty-state__call-to-action .v-icon {
  color: var(--game-accent-secondary);
  font-size: 32px;
}

.swing {
  animation: swing 2s infinite ease-in-out;
}

@keyframes swing {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-15px); }
}

.empty-state__footer {
  margin-top: var(--game-spacing-md);  /* Reduced from xl */
  display: flex;
  justify-content: space-between;
  align-items: center;
  opacity: 0.5;
  font-size: 12px;
}

.pixel-art-cat {
  color: var(--game-text-muted);
}

.status-msg {
  color: var(--game-text-muted);
}
</style>
