<template>
  <div class="sound-selector">
    <div class="sound-selector__row">
      <div class="sound-selector__display" @click="showPicker = true">
        <v-icon size="small" class="sound-selector__icon">mdi-music-note</v-icon>
        <span class="sound-selector__name">{{ modelValue || 'No sound selected' }}</span>
        <v-icon size="small" class="sound-selector__browse">mdi-folder-open</v-icon>
      </div>
      <v-btn icon size="small" @click="toggleSound" :disabled="!modelValue">
        <v-icon size="small">{{ isPlaying ? 'mdi-stop' : 'mdi-play' }}</v-icon>
      </v-btn>
    </div>

    <v-slider
      v-if="modelValue"
      :model-value="volume ?? 100"
      @update:model-value="onVolumeChange"
      :min="1"
      :max="100"
      :step="1"
      append-icon="mdi-volume-high"
      density="compact"
      hide-details
      class="sound-selector__slider"
    />

    <SoundSelectDialog
      v-model="showPicker"
      :files="soundFiles"
      :currentValue="modelValue"
      @select="onSelect"
    />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import SoundManager from '@/utils/SoundManager'
import SoundSelectDialog from './SoundSelectDialog.vue'

export default {
  name: 'SoundSelector',
  components: { SoundSelectDialog },
  props: {
    modelValue: { type: String, default: null },
    volume: { type: Number, default: 100 }
  },
  emits: ['update:modelValue', 'update:volume'],
  data() {
    return {
      showPicker: false,
      isPlaying: false,
      removeSoundListener: null
    }
  },
  computed: {
    ...mapGetters('sounds', ['files']),
    soundFiles() { return this.files }
  },
  mounted() {
    this.removeSoundListener = SoundManager.addListener(isPlaying => {
      this.isPlaying = isPlaying
    })
  },
  beforeUnmount() {
    if (typeof this.removeSoundListener === 'function') {
      this.removeSoundListener()
    }
    SoundManager.stopCurrentSound()
  },
  methods: {
    onSelect(soundPath) {
      this.$emit('update:modelValue', soundPath)
    },
    onVolumeChange(value) {
      SoundManager.setVolume(value)
      this.$emit('update:volume', value)
    },
    toggleSound() {
      if (this.isPlaying) {
        SoundManager.stopCurrentSound()
      } else if (this.modelValue) {
        SoundManager.playSound(this.modelValue, this.volume ?? 100)
      }
    }
  }
}
</script>

<style scoped>
.sound-selector__row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sound-selector__display {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid rgba(127, 127, 127, 0.3);
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}
.sound-selector__display:hover {
  background: rgba(127, 127, 127, 0.08);
}
.sound-selector__name {
  flex: 1;
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}
.sound-selector__icon,
.sound-selector__browse {
  flex-shrink: 0;
  opacity: 0.6;
}
.sound-selector__slider {
  margin-top: 4px;
}
</style>
