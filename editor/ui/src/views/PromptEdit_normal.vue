<template>
  <div class="config-view" >
    <!-- System Prompt Section -->
    <h4>Normal State Prompt</h4>
    <textarea
      id="normalPrompt"
      v-model="normalPrompt"
      placeholder="Enter system prompt here..."
      class="full-height-textarea"
    ></textarea>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  name: 'PropertyView',
  computed: {
    ...mapGetters('maps', ['mapConfig']),
    normalPrompt: {
      get() {
        return this.mapConfig.normal_prompt;
      },
      set(value) {
        // Commit the updated system prompt to the store
        this.updateMapConfig({ ...this.mapConfig, normal_prompt: value });
      },
    },
    
  },
  methods: {
    ...mapActions('maps', ['updateMapConfig']),
  },
};
</script>

<style scoped>
.config-view {
  height: 100%;
  width:100%;
  overflow-y: auto;
  padding: 10px;
  box-sizing: border-box; 
  display: flex;
  flex-direction: column;
}

.config-view textarea {
  width: 100%;
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: vertical; /* Allows vertical resizing only */
  background-color: #f9f9f9;
  flex: 1;
}

</style>
