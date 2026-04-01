<template>
  <v-dialog :model-value="modelValue" max-width="500" @click:outside="cancel" @update:model-value="updateDialog">
    <v-card class="delete-encounter-dialog">
      <DialogHeader
        title="Remove Encounter"
        @close="cancel"
      />
      <v-card-text class="dialog-content">
        <p class="confirm-text">
          Remove encounter <strong>"{{ encounterName }}"</strong>?
        </p>
      </v-card-text>
      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <ThemedButton @click="cancel" variant="secondary">
          Cancel
        </ThemedButton>
        <ThemedButton 
          @click="confirmDelete" 
          variant="reset" 
        >
          Remove
        </ThemedButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import DialogHeader from './DialogHeader.vue';
import ThemedButton from './ThemedButton.vue';

export default {
  name: 'ConfirmEncounterDeleteDialog',
  components: { DialogHeader, ThemedButton },
  
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    encounterId: {
      type: String,
      default: ''
    },
    encounterName: {
      type: String,
      default: ''
    }
  },
  
  emits: ['update:modelValue', 'confirm'],
  
  methods: {
    confirmDelete() {
      this.$emit('confirm', this.encounterId)
      this.$emit('update:modelValue', false)
    },
    
    cancel() {
      this.$emit('update:modelValue', false)
    },
    
    updateDialog(value) {
      this.$emit('update:modelValue', value)
    }
  }
}
</script>

<style scoped>
.confirm-text {
  text-align: center;
}
</style>