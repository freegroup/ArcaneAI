<template>
  <v-dialog :model-value="dialog" max-width="400" @click:outside="closeDialog" @update:model-value="updateDialog">
    <v-card>
      <v-card-title class="headline">Create Map</v-card-title>
      <v-card-text>
        <v-text-field
          ref="nameInput"
          label="Name"
          v-model="mapName"
          :error-messages="nameError"
          @input="validateName"
        ></v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn :disabled="isCreateDisabled" color="primary" text @click="createDialog">Create</v-btn>
        <v-btn text @click="closeDialog">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapActions, mapGetters } from "vuex";

export default {
  props: {
    dialog: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      mapName: "", // Name for the map
      nameError: "", // Error message for the input field
    };
  },
  computed: {
    ...mapGetters("maps", ["maps"]),
    isCreateDisabled() {
      return !this.mapName || this.maps.includes(this.mapName);
    },
  },
  methods: {
    ...mapActions("maps", ["fetchMaps", "createNewMap"]),

    async loadMaps() {
      await this.fetchMaps();
    },

  

    validateName() {
      if (this.maps.includes(this.mapName)) {
        this.nameError = "Name already exists.";
      } else {
        this.nameError = "";
      }
    },

    async createDialog() {
      if (!this.isCreateDisabled) {
        // Create the named map content and store it in Vuex
        await this.createNewMap(this.mapName);
        this.$router.replace({ name: this.$route.name, params: { mapName: this.mapName } });
        this.$emit("update:dialog", false);
        console.log(`Map "${this.mapName}" created!`);  
      }
    },

    closeDialog() {
      this.$emit("update:dialog", false);
      this.mapName = "";
      this.nameError = "";
    },

    updateDialog(value) {
      this.$emit("update:dialog", value);
    },

    focusInput() {
      // Set focus on the input field when dialog opens
      this.$nextTick(() => {
        if (this.$refs.nameInput) {
          this.$refs.nameInput.focus();
        }
      });
    },
  },
  watch: {
    dialog(value) {
      if (value) {
        this.loadMaps();
        this.focusInput(); // Focus the input field when dialog opens
      }
    },
  },
};
</script>

<style scoped></style>
