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
    <ThemedButton 
      @click="handleSend" 
      :disabled="!modelValue.trim() || loading"
      title="Send instruction to AI"
    >
      <v-icon size="small">mdi-magic-staff</v-icon>
      Send
    </ThemedButton>
  </div>
</template>

<script>
import ThemedButton from './ThemedButton.vue';

export default {
  name: 'AIAssistInput',
  components: { ThemedButton },
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
  align-items: center;
}

.prompt-field {
  flex: 1;
  outline: none;
}

.prompt-field:disabled {
  cursor: not-allowed;
}
</style>
