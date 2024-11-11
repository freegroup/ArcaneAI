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

  static setVolume(volume) {
    if (SoundManager.currentAudio) {
      SoundManager.currentAudio.volume = volume / 100; // Update volume while audio is playing
    }
  }
  
  /**
   * Download and play a sound by name. Stops any currently playing sound.
   * @param {string} soundName - The name of the sound to play.
   */
  static async playSound(soundName, volume=100) {
    if (!storeInstance) {
      console.error("SoundManager: Vuex store not initialized.")
      return
    }

    SoundManager.stopCurrentSound()

    const mapName = storeInstance.getters['maps/mapName']
    await storeInstance.dispatch('sounds/downloadSound', {mapName, soundName})
    const soundUrl = storeInstance.getters['sounds/currentSoundUrl']

    if (soundUrl) {
      SoundManager.currentAudio = new Audio(soundUrl)
      SoundManager.currentAudio.volume = volume / 100;
      SoundManager.currentAudio.play()

      SoundManager.currentAudio.onended = () => {
        URL.revokeObjectURL(soundUrl)
        SoundManager.currentAudio = null
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
