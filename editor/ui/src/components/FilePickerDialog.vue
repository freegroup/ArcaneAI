<template>
    <v-dialog :model-value="dialog" max-width="400" @click:outside="closeDialog" @update:model-value="updateDialog">
      <v-card>
        <v-card-title class="headline">Select a Conversation</v-card-title>
        <v-card-text>
          <div class="scrollable-list">
            <ul>
              <li
                v-for="(conversation, index) in conversations"
                :key="index"
                @click="selectConversation(conversation)"
                class="clickable-item"
              >
                {{ conversation }}
              </li>
            </ul>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="closeDialog">Cancel</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>
  
  <script>
  import { mapActions, mapGetters } from 'vuex';
  
  export default {
    props: {
      dialog: {
        type: Boolean,
        required: true,
      },
    },
    computed: {
      ...mapGetters('conversations', ['conversations']),
    },
    methods: {
      ...mapActions('conversations', ['fetchConversations', 'downloadConversation']),
  
      async loadConversations() {
        await this.fetchConversations();
      },
  
      async selectConversation(conversation) {
        // Download the selected conversation content and store it in Vuex
        await this.downloadConversation(conversation);
        this.$router.replace({ name: this.$route.name, params: { fileName: conversation } });
        this.$emit('update:dialog', false); // Close the dialog
      },
  
      closeDialog() {
        this.$emit('update:dialog', false); // Close the dialog
      },
  
      updateDialog(value) {
        this.$emit('update:dialog', value); // Update dialog state in parent
      },
    },
    watch: {
      dialog(value) {
        if (value) {
          this.loadConversations(); // Load conversations when dialog opens
        }
      },
    },
  };
  </script>
  
  <style scoped>
  .scrollable-list {
    max-height: 200px;
    overflow-y: auto;
    border: 1px solid #ddd;
    padding: 10px;
    margin: 0;
  }
  
  .scrollable-list ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .scrollable-list li {
    padding: 10px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .scrollable-list li:hover {
    background-color: #f0f0f0;
  }
  </style>
  