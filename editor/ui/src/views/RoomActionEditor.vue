<template>
  <v-dialog
    v-model="dialogOpen"
    max-width="700px"
    persistent
  >
    <v-card v-if="trigger" class="room-action-editor-dialog">
      <DialogHeader
        title="Action Editor"
        icon="mdi-pencil"
        @close="close"
      />

      <v-card-text class="action-editor__body dialog-content property-view">

        <div class="field-group">
          <PropertyLabel>Name</PropertyLabel>
          <input
            type="text"
            v-model="local.name"
            @input="onChange"
          />
        </div>

        <div class="field-group">
          <PropertyLabel>Sound Effect</PropertyLabel>
          <SoundSelector
            :modelValue="local.sound_effect"
            :volume="local.sound_effect_volume"
            @update:modelValue="val => { local.sound_effect = val; onChange() }"
            @update:volume="val => { local.sound_effect_volume = val; onChange() }"
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
          </div>
        </div>

        <div class="field-group">
          <PropertyLabel>Description</PropertyLabel>
          <textarea
            v-model="local.description"
            placeholder="What can the player do here?"
            rows="3"
            @input="onChange"
          ></textarea>
        </div>

        <div class="field-group">
          <PropertyLabel>On Success</PropertyLabel>
          <textarea
            v-model="local.system_prompt"
            placeholder="What happens when the action succeeds?"
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
import { mapActions } from 'vuex'
import SoundManager from '@/utils/SoundManager'
import SoundSelector from '@/components/SoundSelector.vue'
import DialogHeader from '@/components/DialogHeader.vue'
import ThemedButton from '@/components/ThemedButton.vue'
import PropertyLabel from '@/components/PropertyLabel.vue'

export default {
  name: 'RoomActionEditor',
  components: { SoundSelector, DialogHeader, ThemedButton, PropertyLabel },
  props: {
    modelValue: { type: Boolean, default: false },
    trigger: { type: Object, default: null }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      local: this.makeEmpty(),
      conditionsText: '',
      actionsText: '',
      isInitializing: false
    }
  },
  computed: {
    dialogOpen: {
      get() { return this.modelValue },
      set(v) { this.$emit('update:modelValue', v) }
    }
  },
  watch: {
    trigger: {
      immediate: true,
      handler(t) {
        this.isInitializing = true
        if (t) {
          this.local = {
            id: t.id,
            name: t.name || '',
            description: t.description || '',
            system_prompt: t.system_prompt || '',
            sound_effect: t.sound_effect || '',
            sound_effect_volume: t.sound_effect_volume ?? 100,
            sound_effect_duration: t.sound_effect_duration ?? 2,
            conditions: Array.isArray(t.conditions) ? [...t.conditions] : [],
            actions: Array.isArray(t.actions) ? [...t.actions] : []
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
  },
  beforeUnmount() {
    SoundManager.stopCurrentSound()
  },
  methods: {
    ...mapActions('model', ['updateTrigger']),
    makeEmpty() {
      return {
        id: null, name: '', description: '', system_prompt: '',
        sound_effect: '', sound_effect_volume: 100, sound_effect_duration: 2,
        conditions: [], actions: []
      }
    },
    onChange() {
      if (this.isInitializing || !this.local.id) return
      // model/updateTrigger expects a TriggerLabel-shaped payload (text + userData)
      // — same shape as in StateTriggerProperty.vue.
      this.updateTrigger({
        id: this.local.id,
        name: this.local.name,
        userData: {
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
.field-group textarea { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85rem; }
.sound-controls { margin-top: 8px; display: flex; flex-direction: column; gap: 4px; }
.sound-control-row { display: flex; align-items: center; gap: 8px; }
.sound-control-icon { flex-shrink: 0; }
</style>
