// SoundManager.js
let storeInstance = null;

class SoundManager {
  static currentAudio = null; // Store the current audio instance

  /**
   * Initialize SoundManager with a Vuex store instance.
   * @param {Object} store - The Vuex store instance.
   */
  static initialize(store) {
    storeInstance = store;
  }

  /**
   * Download and play a sound by name. Stops any currently playing sound.
   * @param {string} soundName - The name of the sound to play.
   */
  static async playSound(soundName) {
    if (!storeInstance) {
      console.error("SoundManager: Vuex store not initialized.");
      return;
    }

    // Stop the current audio if it's playing
    SoundManager.stopCurrentSound();

    // Download sound and retrieve URL from Vuex store
    await storeInstance.dispatch('sounds/downloadSound', soundName);
    const soundUrl = storeInstance.getters['sounds/currentSoundUrl'];

    if (soundUrl) {
      // Create a new audio instance and play it
      SoundManager.currentAudio = new Audio(soundUrl);
      SoundManager.currentAudio.play();

      // Clean up the audio instance when playback ends
      SoundManager.currentAudio.onended = () => {
        URL.revokeObjectURL(soundUrl);
        SoundManager.currentAudio = null;
      };
    }
  }

  /**
   * Stop the currently playing sound, if any.
   */
  static stopCurrentSound() {
    if (SoundManager.currentAudio) {
      SoundManager.currentAudio.pause();
      SoundManager.currentAudio.currentTime = 0;
      SoundManager.currentAudio = null;
    }
  }
}

export default SoundManager;
