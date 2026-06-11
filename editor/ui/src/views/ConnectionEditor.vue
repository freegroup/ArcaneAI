<template>
  <v-dialog
    v-model="dialogOpen"
    max-width="700px"
    persistent
  >
    <v-card v-if="exit" class="room-action-editor-dialog">
      <DialogHeader
        icon="mdi-pencil"
        @close="close"
      >
        <span class="conn-header">
          <span class="conn-header__title">Transition Editor</span>
          <span class="conn-header__route">
            <span class="conn-header__room">{{ sourceRoomName }}</span>
            <span class="conn-header__arrow">────▶</span>
            <span class="conn-header__room">{{ targetRoomName }}</span>
          </span>
        </span>
      </DialogHeader>

      <v-card-text class="action-editor__body dialog-content property-view">

        <div class="field-group">
          <PropertyLabel>Name</PropertyLabel>
          <input
            type="text"
            v-model="local.name"
            @input="onNameInput"
          />
        </div>

        <div class="field-group">
          <PropertyLabel>Sound Effect</PropertyLabel>
          <div class="sound-selection">
            <div class="sound-display" @click="showSoundPicker = true">
              <span class="sound-name">{{ local.sound_effect || 'No sound selected' }}</span>
              <v-icon size="small">mdi-folder-open</v-icon>
            </div>
            <v-btn icon size="small" @click="toggleSound" :disabled="!local.sound_effect">
              <v-icon size="small">{{ isPlaying ? 'mdi-stop' : 'mdi-play' }}</v-icon>
            </v-btn>
          </div>

          <SoundSelectDialog
            v-model="showSoundPicker"
            :files="soundFiles"
            :currentValue="local.sound_effect"
            @select="onSoundSelected"
          />

          <div class="sound-controls" v-if="local.sound_effect">
            <div class="sound-control-row">
              <v-text-field
                v-model.number="local.sound_effect_duration"
                label="Duration"
                suffix="seconds"
                density="compact"
                type="number"
                min="0"
                max="600"
                hide-details
                @input="onChange"
              />
              <v-icon class="sound-control-icon">mdi-clock</v-icon>
            </div>
            <div class="sound-control-row">
              <v-slider
                v-model="local.sound_effect_volume"
                :min="1"
                :max="100"
                :step="1"
                hide-details
                @end="onChange"
              />
              <v-icon class="sound-control-icon">mdi-volume-high</v-icon>
            </div>
          </div>
        </div>

        <div class="field-group">
          <PropertyLabel>Description</PropertyLabel>
          <textarea
            v-model="local.description"
            placeholder="What does the player see at this exit?"
            rows="3"
            @input="onChange"
          ></textarea>
        </div>

        <div class="field-group">
          <PropertyLabel>On Success</PropertyLabel>
          <textarea
            v-model="local.system_prompt"
            placeholder="What happens when the player takes this exit?"
            rows="3"
            @input="onChange"
          ></textarea>
        </div>

        <div class="field-group">
          <PropertyLabel>Conditions</PropertyLabel>
          <textarea
            v-model="conditionsText"
            placeholder="e.g. has_key == true (one per line)"
            rows="2"
            @input="onConditionsChange"
          ></textarea>
        </div>

        <div class="field-group">
          <PropertyLabel>Actions (Effects)</PropertyLabel>
          <textarea
            v-model="actionsText"
            placeholder="e.g. coins = coins + 1 (one per line)"
            rows="2"
            @input="onActionsChange"
          ></textarea>
        </div>

      </v-card-text>

      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <ThemedButton @click="close" variant="secondary">
          Close
        </ThemedButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import SoundManager from '@/utils/SoundManager'
import SoundSelectDialog from '@/components/SoundSelectDialog.vue'
import DialogHeader from '@/components/DialogHeader.vue'
import ThemedButton from '@/components/ThemedButton.vue'
import PropertyLabel from '@/components/PropertyLabel.vue'

export default {
  name: 'ConnectionEditor',
  components: { SoundSelectDialog, DialogHeader, ThemedButton, PropertyLabel },
  props: {
    modelValue: { type: Boolean, default: false },
    exit: { type: Object, default: null },
    /**
     * Source state ID — the room this exit leaves from. Required to keep the
     * connection's source intact when we rebuild and dispatch updateConnection.
     */
    sourceId: { type: String, default: null }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      local: this.makeEmpty(),
      conditionsText: '',
      actionsText: '',
      showSoundPicker: false,
      isPlaying: false,
      removeSoundListener: null,
      isInitializing: false
    }
  },
  computed: {
    ...mapGetters('sounds', ['files']),
    ...mapGetters('model', ['allStates', 'getConnection']),
    soundFiles() { return this.files },
    dialogOpen: {
      get() { return this.modelValue },
      set(v) { this.$emit('update:modelValue', v) }
    },
    resolvedRoomName() {
      const id = this.local?.targetId
      if (!id) return '—'
      const s = this.allStates.find(s => s.id === id)
      return s?.name || id
    },
    sourceRoomName() {
      const id = this.local?.sourceId
      if (!id) return '?'
      const s = this.allStates.find(s => s.id === id)
      return s?.name || '?'
    },
    targetRoomName() {
      const id = this.local?.targetId
      if (!id) return '?'
      const s = this.allStates.find(s => s.id === id)
      return s?.name || '?'
    },
    targetOptions() {
      // Sorted list of all rooms — user picks one as the new target.
      // Exclude the current source room: an exit pointing back to itself
      // would be an action, not a room transition.
      return [...this.allStates]
        .filter(s => s && s.id && s.name && s.id !== this.sourceId)
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(s => ({ id: s.id, name: s.name }))
    }
  },
  watch: {
    exit: {
      immediate: true,
      handler(e) {
        this.isInitializing = true
        if (e) {
          // Fetch full connection from model store to get userData (sound, system_prompt, ...)
          const conn = this.getConnection(e.id) || {}
          const ud = conn.userData || {}
          this.local = {
            id: e.id,
            name: e.name || conn.name || '',
            sourceId: e.sourceId || conn.source?.node || null,
            targetId: e.targetId || conn.target?.node || null,
            description: ud.description || '',
            system_prompt: ud.system_prompt || '',
            sound_effect: ud.sound_effect || '',
            sound_effect_volume: ud.sound_effect_volume ?? 100,
            sound_effect_duration: ud.sound_effect_duration ?? 2,
            conditions: Array.isArray(ud.conditions) ? [...ud.conditions] : [],
            actions: Array.isArray(ud.actions) ? [...ud.actions] : []
          }
          this.conditionsText = this.local.conditions.join('\n')
          this.actionsText = this.local.actions.join('\n')
        } else {
          this.local = this.makeEmpty()
        }
        this.$nextTick(() => { this.isInitializing = false })
      }
    }
  },
  mounted() {
    this.removeSoundListener = SoundManager.addListener((p) => { this.isPlaying = p })
  },
  beforeUnmount() {
    if (typeof this.removeSoundListener === 'function') this.removeSoundListener()
    SoundManager.stopCurrentSound()
  },
  methods: {
    ...mapActions('model', ['updateConnection']),
    makeEmpty() {
      return {
        id: null, name: '', sourceId: null, targetId: null,
        description: '', system_prompt: '',
        sound_effect: '', sound_effect_volume: 100, sound_effect_duration: 2,
        conditions: [], actions: []
      }
    },
    onNameInput(event) {
      // Same sanitization rule as ConnectionTriggerProperty.vue: spaces -> _, only [a-zA-Z0-9_-]
      const input = event.target
      const cursorPos = input.selectionStart
      const newValue = (this.local.name || '').replace(/ /g, '_').replace(/[^a-zA-Z0-9_-]/g, '')
      if (newValue !== this.local.name) {
        this.local.name = newValue
        this.$nextTick(() => input.setSelectionRange(cursorPos, cursorPos))
      }
      this.onChange()
    },
    onChange() {
      if (this.isInitializing || !this.local.id) return
      // Rebuild connection payload preserving source/target structure expected by model.js
      const existing = this.getConnection(this.local.id) || {}
      this.updateConnection({
        ...existing,
        id: this.local.id,
        name: this.local.name,
        type: existing.type || 'TriggerConnection',
        source: existing.source || (this.sourceId ? { node: this.sourceId } : undefined),
        target: { ...(existing.target || {}), node: this.local.targetId },
        userData: {
          ...(existing.userData || {}),
          description: this.local.description,
          system_prompt: this.local.system_prompt,
          sound_effect: this.local.sound_effect,
          sound_effect_volume: this.local.sound_effect_volume,
          sound_effect_duration: this.local.sound_effect_duration,
          conditions: this.local.conditions,
          actions: this.local.actions
        }
      })
    },
    onConditionsChange() {
      const text = this.conditionsText?.trim()
      this.local.conditions = (!text || text.split('\n').every(l => !l.trim()))
        ? []
        : text.split('\n').map(l => l.trim())
      this.onChange()
    },
    onActionsChange() {
      this.local.actions = this.actionsText?.split('\n') ?? []
      this.onChange()
    },
    onSoundSelected(soundPath) {
      this.local.sound_effect = soundPath
      this.onChange()
    },
    toggleSound() {
      if (this.isPlaying) {
        SoundManager.stopCurrentSound()
      } else if (this.local.sound_effect) {
        SoundManager.playSound(
          this.local.sound_effect,
          this.local.sound_effect_volume || 100,
          this.local.sound_effect_duration || null
        )
      }
    },
    close() {
      SoundManager.stopCurrentSound()
      this.dialogOpen = false
    }
  }
}
</script>

<style scoped>
.action-editor__body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 16px;
  max-height: 70vh;
  overflow-y: auto;
}
.field-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field-group label {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.75;
}
.field-group input,
.field-group textarea {
  width: 100%;
  padding: 6px 10px;
  font: inherit;
  background: rgba(127, 127, 127, 0.08);
  border: 1px solid rgba(127, 127, 127, 0.3);
  border-radius: 4px;
  color: inherit;
  resize: vertical;
}
.field-group textarea {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.85rem;
}
.sound-selection { display: flex; align-items: center; gap: 6px; }
.sound-display {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid rgba(127, 127, 127, 0.3);
  border-radius: 4px;
  cursor: pointer;
}
.sound-display:hover { background: rgba(127, 127, 127, 0.08); }
.sound-name { flex: 1; font-size: 0.85rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sound-controls { margin-top: 8px; display: flex; flex-direction: column; gap: 4px; }
.sound-control-row { display: flex; align-items: center; gap: 8px; }
.sound-control-icon { flex-shrink: 0; }
.readonly-field {
  padding: 6px 10px;
  border: 1px solid rgba(127,127,127,0.3);
  border-radius: 4px;
  font-size: 0.9rem;
  opacity: 0.75;
  font-style: italic;
}
.conn-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.conn-header__title {
  font-size: 1.1rem;
  font-weight: 600;
  letter-spacing: 0.03em;
}
.conn-header__route {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  opacity: 0.65;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  letter-spacing: 0.02em;
  overflow: hidden;
}
.conn-header__room {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}
.conn-header__arrow {
  flex-shrink: 0;
  opacity: 0.5;
}
</style>
