/**
 * SpeechHandler - Handles TTS audio messages and plays speech
 * Combines message handling with audio playback logic
 */
class SpeechHandler {
    constructor() {
        this.audioContext = null;
        this.currentSource = null;
        this.accumulatedChunks = [];
        this.isPlaying = false;
    }

    /**
     * Initialize AudioContext (lazy, requires user interaction)
     */
    initAudioContext() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
        }
    }

    /**
     * Handle binary audio data (PCM from TTS via WebSocket)
     * @param {ArrayBuffer} arrayBuffer - Raw PCM audio data
     */
    handleBinaryAudio(arrayBuffer) {
        this.initAudioContext();
        this.accumulatedChunks.push(new Int16Array(arrayBuffer));
        if (!this.isPlaying) {
            this.playNextInQueue();
        }
    }

    /**
     * Handle speak stop message
     */
    handleStop() {
        console.log('[SPEECH] Stop');
        this.accumulatedChunks = [];
        this.isPlaying = false;
        if (this.currentSource) {
            this.currentSource.onended = null;
            try {
                this.currentSource.stop();
            } catch (e) {
                // Already stopped
            }
            this.currentSource = null;
        }
    }

    /**
     * Play accumulated audio chunks
     */
    playNextInQueue() {
        if (this.accumulatedChunks.length === 0) {
            this.isPlaying = false;
            return;
        }

        // Concatenate all chunks
        const totalLength = this.accumulatedChunks.reduce((acc, chunk) => acc + chunk.length, 0);
        const concatenatedData = new Int16Array(totalLength);
        let offset = 0;
        for (const chunk of this.accumulatedChunks) {
            concatenatedData.set(chunk, offset);
            offset += chunk.length;
        }
        this.accumulatedChunks = [];

        // Create audio buffer
        const audioBuffer = this.audioContext.createBuffer(1, concatenatedData.length, 24000);
        const channelData = audioBuffer.getChannelData(0);
        for (let i = 0; i < concatenatedData.length; i++) {
            channelData[i] = concatenatedData[i] / 32768;
        }

        // Play audio
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);
        source.playbackRate.value = 1.05;
        source.onended = () => this.playNextInQueue();
        source.start();

        this.currentSource = source;
        this.isPlaying = true;
    }

    /**
     * Check if currently speaking
     * @returns {boolean}
     */
    isSpeaking() {
        return this.isPlaying;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SpeechHandler;
}