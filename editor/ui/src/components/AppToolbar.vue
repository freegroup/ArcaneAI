<template>
  <v-app-bar color="primary" dark >
    <v-btn icon>
      <v-icon>mdi-home</v-icon>
    </v-btn>
    <v-btn text @click="openFileDialog">Load</v-btn>
    <v-btn text @click="save">Save</v-btn> 
    <v-spacer></v-spacer>

    <FilePickerDialog v-model:dialog="filePickerDialog" />

</v-app-bar>
</template>

<script>
import { mapActions } from 'vuex';
import FilePickerDialog from './FilePickerDialog.vue';

export default {
  components: {
    FilePickerDialog,
  },
  data() {
    return {
      filePickerDialog: false,
    };
  },
  methods: {
    ...mapActions('conversations', ['saveConversation']),

    openFileDialog() {
      this.filePickerDialog = true;
    },
    save() {
      console.log("Save Document");
      this.saveConversation();
    },
  },
};
</script>

<style scoped>
/* Optional custom styles */
</style>
