<template>
  <v-dialog v-model="isOpen" max-width="600px" @click:outside="close">
    <v-card class="help-dialog">
      <DialogHeader 
        :title="title" 
        @close="close" 
      />

      <v-card-text class="help-dialog-content" v-html="helpText">
      </v-card-text>

      <v-card-actions class="help-dialog-actions">
        <v-spacer></v-spacer>
        <ThemedButton @click="close" variant="proceed">
          Got it!
        </ThemedButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import DialogHeader from './DialogHeader.vue';
import ThemedButton from './ThemedButton.vue';

export default {
  name: 'ExtendedHelpDialog',
  components: { DialogHeader, ThemedButton },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      required: true
    },
    helpText: {
      type: String,
      required: true
    }
  },
  computed: {
    isOpen: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    }
  },
  methods: {
    close() {
      this.isOpen = false;
    }
  }
};
</script>

<style scoped>
.help-dialog-content {
  overflow-y: auto;
}

.help-dialog-content :deep(strong) {
  font-weight: 100;
}

.help-dialog-content :deep(pre) {
  overflow-x: auto;
}
</style>