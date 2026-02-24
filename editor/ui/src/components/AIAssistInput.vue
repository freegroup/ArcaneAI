<template>
  <div class="ai-assist-input">
    <input
      ref="input"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
      type="text"
      :placeholder="placeholder"
      @keyup.enter="handleSend"
      :disabled="loading"
      class="prompt-field"
    />
    <RetroButton 
      @click="handleSend" 
      :disabled="!modelValue.trim() || loading"
      title="Send instruction to AI"
    >
      <v-icon size="small">mdi-magic-staff</v-icon>
      Send
    </RetroButton>
  </div>
</template>

<script>
import RetroButton from './RetroButton.vue';

export default {
  name: 'AIAssistInput',
  components: { RetroButton },
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    loading: {
      type: Boolean,
      default: false
    },
    placeholder: {
      type: String,
      default: "How shall I improve the text?"
    }
  },
  emits: ['update:modelValue', 'send'],
  methods: {
    handleSend() {
      if (this.modelValue.trim() && !this.loading) {
        this.$emit('send');
      }
    },
    focus() {
      if (this.$refs.input) {
        this.$refs.input.focus();
      }
    }
  }
};
</script>

<style scoped>
.ai-assist-input {
  display: flex;
  gap: var(--game-spacing-sm);
  align-items: center;
}

.prompt-field {
  flex: 1;
  padding: var(--game-spacing-sm) var(--game-spacing-md);
  background: var(--game-input-bg);
  border: 1px solid var(--game-input-border);
  border-radius: 0;
  color: var(--game-text-primary);
  font-size: var(--game-font-size-md);
  outline: none;
  font-family: inherit;
  letter-spacing: 1px;
}

.prompt-field:focus {
  border-color: var(--game-input-focus);
}

.prompt-field:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.prompt-field::placeholder {
  color: var(--game-text-muted);
}
</style>
