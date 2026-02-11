// SoundManager.js
let storeInstance = null;

class SoundManager {
  static currentAudio = null; // Store the current audio instance
  static listeners = []; // Event listeners for play/stop events

  /**
   * Initialize SoundManager with a Vuex store instance.
   * @param {Object} store - The Vuex store instance.
   */
  static initialize(store) {
    storeInstance = store;
  }

  /**
   * Add event listener for sound state changes
   * @param {Function} callback - Callback function(isPlaying)
   * @returns {Function} - Cleanup function to remove listener
   */
  static addListener(callback) {
    SoundManager.listeners.push(callback);
    // Return cleanup function
    return () => {
      const index = SoundManager.listeners.indexOf(callback);
      if (index > -1) {
        SoundManager.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Notify all listeners about sound state change
   * @param {boolean} isPlaying - Whether sound is currently playing
   */
  static notifyListeners(isPlaying) {
    SoundManager.listeners.forEach(callback => callback(isPlaying));
  }

  /**
   * Check if sound is currently playing
   * @returns {boolean}
   */
  static isPlaying() {
    return SoundManager.currentAudio !== null && !SoundManager.currentAudio.paused;
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
      
      // Notify listeners that sound is playing
      SoundManager.notifyListeners(true);

      SoundManager.currentAudio.onended = () => {
        URL.revokeObjectURL(soundUrl)
        SoundManager.currentAudio = null
        // Notify listeners that sound stopped
        SoundManager.notifyListeners(false);
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
      // Notify listeners that sound stopped
      SoundManager.notifyListeners(false);
    }
  }
}

export default SoundManager;
