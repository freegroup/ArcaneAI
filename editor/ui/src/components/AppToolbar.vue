<template>
  <v-app-bar border dark >
    <v-btn icon>
      <v-icon>mdi-home</v-icon>
    </v-btn>
    <v-btn text @click="newFileDialog">New</v-btn>
    <v-btn text @click="openFileDialog">Load</v-btn>
    <v-btn text @click="save">Save</v-btn> 
    <v-spacer></v-spacer>

    <FilePickerDialog v-model:dialog="filePickerDialog" />
    <FileNewDialog    v-model:dialog="fileNewDialog" />

</v-app-bar>
</template>

<script>
import { mapActions } from 'vuex';
import FileNewDialog from './FileNewDialog.vue';
import FilePickerDialog from './FilePickerDialog.vue';

export default {
  components: {
    FilePickerDialog,
    FileNewDialog,
  },
  data() {
    return {
      filePickerDialog: false,
      fileNewDialog: false,
    };
  },
  methods: {
    ...mapActions('maps', ['saveMap']),
    
    newFileDialog() {
      this.fileNewDialog = true;
    },
    
    openFileDialog() {
      this.filePickerDialog = true;
    },
    
    save() {
      console.log("Save Map");
      this.saveMap();
    },
  },
};
</script>

<style scoped>
/* Optional custom styles */
</style>
