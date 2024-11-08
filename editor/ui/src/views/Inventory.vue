<template>
  <v-container>

    <!-- Inventory Section -->
    <h4>Inventory</h4>
    <v-row class="align-center">
      <v-col cols="3">
        <v-text-field
          v-model="newItem.key"
          label="New Item Key"
          placeholder="Enter key"
          outlined
          dense
          full-width
        ></v-text-field>
      </v-col>
      <v-col cols="3">
        <v-text-field
          v-model="newItem.value"
          label="New Item Value"
          placeholder="Enter value"
          outlined
          dense
          full-width
        ></v-text-field>
      </v-col>
      <v-col cols="3">
        <v-select
          v-model="newItem.type"
          :items="['string', 'boolean', 'integer']"
          label="Type"
          outlined
          dense
          full-width
        ></v-select>
      </v-col>
      <v-col cols="3" class="d-flex align-center">
        <v-btn @click="addItem" color="primary" block>Add Item</v-btn>
      </v-col>
    </v-row>

    <!-- Inventory Table -->
    <v-table density="compact">
      <thead>
        <tr>
          <th>Key</th>
          <th>Value</th>
          <th>Type</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, key) in inventory" :key="key">
          <td>{{ item.key }}</td>
          <td>
            <v-text-field
              v-model="item.value"
              :type="item.type === 'integer' ? 'number' : 'text'"
              @change="updateInventory"
              outlined
               density="compact"
              full-width
            ></v-text-field>
          </td>
          <td>
            <v-select
              v-model="item.type"
              :items="['string', 'boolean', 'integer']"
              @change="updateInventory"
              outlined
              density="compact"
              full-width
            ></v-select>
          </td>
          <td>
            <v-btn  size="small" icon @click="removeItem(item.key)">
              <v-icon  size="small" color="red">mdi-delete</v-icon>
            </v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>
  </v-container>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  name: 'InventoryView',
  data() {
    return {
      newItem: { key: '', value: '', type: 'string' }, // New item to be added with type
    };
  },
  computed: {
    ...mapGetters('conversations', ['conversationConfig']),
    inventory: {
      get() {
        // Return inventory items as an array with key, value, and type
        return this.conversationConfig.inventory || [];
      },
      set(value) {
        this.updateConversationConfig({
          ...this.conversationConfig,
          inventory: value,
        });
      },
    },
  },
  methods: {
    ...mapActions('conversations', ['updateConversationConfig']),
    
    addItem() {
      if (this.newItem.key && this.newItem.value !== undefined) {
        // Convert value to the appropriate type
        this.newItem.value = this.convertType(this.newItem.value, this.newItem.type);

        // Add the new item to inventory
        const updatedInventory = [...this.inventory, { ...this.newItem }];

        // Update the Vuex store
        this.inventory = updatedInventory;
        
        // Reset the form
        this.newItem = { key: '', value: '', type: 'string' };
      }
    },

    updateInventory() {
      // Ensure values are updated based on their type
      this.inventory.forEach(item => {
        item.value = this.convertType(item.value, item.type);
      });
      
      // Update Vuex store
      this.updateConversationConfig({
        ...this.conversationConfig,
        inventory: [...this.inventory],
      });
    },

    removeItem(key) {
      // Filter out the item with the specified key
      const updatedInventory = this.inventory.filter(item => item.key !== key);
      
      // Update Vuex store
      this.inventory = updatedInventory;
    },

    convertType(value, type) {
      switch (type) {
        case 'boolean':
          return value === 'true' || value === true;
        case 'integer':
          return parseInt(value) || 0;
        default:
          return String(value);
      }
    },
  },
};
</script>

<style scoped>
.v-textarea,
.v-text-field {
  width: 100%;
}

::v-deep .v-input__details {
  display: none;
}

.v-btn {
  text-transform: uppercase;
}

.align-center {
  align-items: center;
}
</style>
