/**
 * JukeboxHandler - Handles sound messages and plays audio
 * Combines message handling with audio playback logic
 */
class JukeboxHandler {
    constructor(baseUri = '') {
        this.baseUri = baseUri;
        this.ambientAudio = null;
        this.effectAudio = null;
        this.effectTimeout = null;
    }

    /**
     * Handle ambient sound message - plays looping background audio
     * @param {Object} data - { sound_file, volume }
     */
    handleAmbient(data) {
        console.log('[JUKEBOX] Ambient:', data);

        // Stop current ambient
        this.stopAmbient();

        if (!data.sound_file) return;

        this.ambientAudio = new Audio(`${this.baseUri}/soundfx/${data.sound_file}`);
        this.ambientAudio.loop = true;
        this.ambientAudio.volume = (data.volume || 100) / 100;
        this.ambientAudio.play().catch(e => console.warn('[JUKEBOX] Ambient autoplay blocked:', e));
    }

    /**
     * Handle sound effect message - plays one-shot audio
     * @param {Object} data - { sound_file, volume, duration }
     */
    handleEffect(data) {
        console.log('[JUKEBOX] Effect:', data);

        // Stop previous effect
        this.stopEffect();

        if (!data.sound_file) return;

        this.effectAudio = new Audio(`${this.baseUri}/soundfx/${data.sound_file}`);
        this.effectAudio.volume = (data.volume || 100) / 100;
        this.effectAudio.play().catch(e => console.warn('[JUKEBOX] Effect autoplay blocked:', e));

        // Stop after duration if specified
        if (data.duration && data.duration > 0) {
            this.effectTimeout = setTimeout(() => {
                this.stopEffect();
            }, data.duration * 1000);
        }
    }

    /**
     * Stop ambient sound
     */
    stopAmbient() {
        if (this.ambientAudio) {
            this.ambientAudio.pause();
            this.ambientAudio = null;
        }
    }

    /**
     * Stop sound effect
     */
    stopEffect() {
        if (this.effectTimeout) {
            clearTimeout(this.effectTimeout);
            this.effectTimeout = null;
        }
        if (this.effectAudio) {
            this.effectAudio.pause();
            this.effectAudio = null;
        }
    }

    /**
     * Stop all sounds
     */
    stopAll() {
        this.stopAmbient();
        this.stopEffect();
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JukeboxHandler;
}