<template>
  <div class="config-view" >
    <!-- System Prompt Section -->
    <h4>End State Prompt</h4>
    <textarea
      id="endPrompt"
      v-model="endPrompt"
      placeholder="Enter system prompt here..."
      class="full-height-textarea"
    ></textarea>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  name: 'EndGameView',
  computed: {
    ...mapGetters('maps', ['mapConfig']),
    endPrompt: {
      get() {
        return this.mapConfig.end_prompt;
      },
      set(value) {
        // Commit the updated system prompt to the store
        this.updateMapConfig({ ...this.mapConfig, end_prompt: value });
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
