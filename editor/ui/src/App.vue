<template>
  <v-app id="app">
    <application-header
      :show-toolbar="!!currentGameName"
      @new-game="gameNewDialog = true"
      @load-game="gameSelectDialog = true"
    />

    <!-- Navigation Drawer - Only show if a game is loaded -->
    <v-navigation-drawer
      v-if="currentGameName"
      permanent
      :rail="isCompact"
      :width="drawerWidth"
      class="nav-drawer"
    >
      <!-- Toggle button -->
      <v-list-item
        @click="toggleDrawerCompact"
        class="nav-drawer__toggle"
      >
        <template v-slot:prepend>
          <v-icon :icon="isCompact ? 'mdi-chevron-right' : 'mdi-chevron-left'"></v-icon>
        </template>
      </v-list-item>

      <!-- Game Name Display -->
      <div v-if="!isCompact && currentGameName" class="nav-drawer__game-name">
        <span class="nav-drawer__game-label">{{ currentGameName }}</span>
      </div>

      <v-divider v-if="!isCompact"></v-divider>

      <v-list
        density="compact"
        class="nav-drawer__list"
        :opened="openSections"
        open-strategy="single"
      >
        <!-- ============ GAME SETUP ============ -->
        <v-list-group value="setup">
          <template v-slot:activator="{ props }">
            <v-list-item
              v-bind="props"
              :title="isCompact ? undefined : 'Game Setup'"
              class="nav-drawer__item nav-drawer__header"
            />
          </template>

          <v-list-item
            v-if="!isCompact"
            :to="`/game/${currentGameName}/personality`"
            title="Personality"
            class="nav-drawer__subitem"
          >
            <template v-slot:prepend>
              <span class="nav-drawer__bullet">-</span>
            </template>
          </v-list-item>
          <v-list-item
            v-if="!isCompact"
            :to="`/game/${currentGameName}/welcome`"
            title="Welcome"
            class="nav-drawer__subitem"
          >
            <template v-slot:prepend>
              <span class="nav-drawer__bullet">-</span>
            </template>
          </v-list-item>
          <v-list-item
            v-if="!isCompact"
            :to="`/game/${currentGameName}/game-target`"
            title="Game Target"
            class="nav-drawer__subitem"
          >
            <template v-slot:prepend>
              <span class="nav-drawer__bullet">-</span>
            </template>
          </v-list-item>
          <v-list-item
            v-if="!isCompact"
            :to="`/game/${currentGameName}/help-text`"
            title="Help Text"
            class="nav-drawer__subitem"
          >
            <template v-slot:prepend>
              <span class="nav-drawer__bullet">-</span>
            </template>
          </v-list-item>
          <v-list-item
            v-if="!isCompact"
            :to="`/game/${currentGameName}/inventory`"
            title="Inventory"
            class="nav-drawer__subitem"
          >
            <template v-slot:prepend>
              <span class="nav-drawer__bullet">-</span>
            </template>
          </v-list-item>
        </v-list-group>

        <!-- ============ MAPS ============ -->
        <v-list-group value="maps">
          <template v-slot:activator="{ props }">
            <v-list-item
              v-bind="props"
              :title="isCompact ? undefined : 'Maps'"
              class="nav-drawer__item nav-drawer__header"
            >
              <template v-slot:append v-if="!isCompact">
                <ThemedActionButton
                  @click.stop="openAddEncounterDialog"
                  variant="success"
                  class="nav-drawer__add-btn"
                  title="Add new encounter"
                >+</ThemedActionButton>
              </template>
            </v-list-item>
          </template>

          <v-list-item
            v-if="!isCompact"
            :to="`/game/${currentGameName}/world`"
            title="World"
            class="nav-drawer__subitem"
          >
            <template v-slot:prepend>
              <span class="nav-drawer__bullet">-</span>
            </template>
            <template v-slot:append>
              <v-badge
                v-if="getOpenTodosForWorld() > 0"
                :content="getOpenTodosForWorld()"
                color="warning"
                inline
              ></v-badge>
              <span class="nav-drawer__delete-spacer"></span>
            </template>
          </v-list-item>

          <v-list-item
            v-for="encounter in encountersList"
            v-show="!isCompact"
            :key="encounter"
            :to="`/game/${currentGameName}/encounter/${encounter}`"
            :title="getEncounterDisplayName(encounter)"
            class="nav-drawer__subitem"
          >
            <template v-slot:prepend>
              <span class="nav-drawer__bullet">-</span>
            </template>
            <template v-slot:append>
              <v-badge
                v-if="getOpenTodosForEncounter(encounter) > 0"
                :content="getOpenTodosForEncounter(encounter)"
                color="warning"
                inline
              ></v-badge>
              <ThemedActionButton
                @click.stop.prevent="openDeleteDialog(encounter)"
                variant="danger"
                class="nav-drawer__delete-btn"
                title="Delete encounter"
              >-</ThemedActionButton>
            </template>
          </v-list-item>
        </v-list-group>

        <!-- ============ ROOMS ============ -->
        <v-list-group value="rooms">
          <template v-slot:activator="{ props }">
            <v-list-item
              v-bind="props"
              :title="isCompact ? undefined : 'Rooms'"
              class="nav-drawer__item nav-drawer__header"
            />
          </template>

          <v-list-item
            v-for="room in roomsList"
            v-show="!isCompact"
            :key="room.id"
            :to="`/game/${currentGameName}/rooms/${room.name}`"
            :title="room.name"
            class="nav-drawer__subitem"
          >
            <template v-slot:prepend>
              <span class="nav-drawer__bullet">-</span>
            </template>
          </v-list-item>
        </v-list-group>

        <!-- ============ HELP (disabled placeholder) ============ -->
        <v-list-item
          :title="isCompact ? undefined : 'Help'"
          class="nav-drawer__item nav-drawer__help-disabled"
          disabled
        />
      </v-list>
    </v-navigation-drawer>

    <v-main class="content-area">
      <!-- Show welcome/empty state if no game is loaded -->
      <ArcaneAIEmptyState
        v-if="!currentGameName"
        @new-game="gameNewDialog = true"
        @load-game="gameSelectDialog = true"
      />

      <!-- Otherwise show the actual content -->
      <router-view v-else :key="$route.fullPath"></router-view>
    </v-main>

    <!-- Delete Encounter Dialog -->
    <confirm-encounter-delete-dialog
      v-model="deleteDialogVisible"
      :encounter-id="deletingEncounterId"
      :encounter-name="deletingEncounterName"
      @confirm="handleEncounterDelete"
    />

    <!-- Add Encounter Dialog - available globally when game is loaded -->
    <EncounterNewDialog v-model="showEncounterDialog" />

    <!-- Game Dialogs - available from header and empty state -->
    <GameSelectDialog v-model:dialog="gameSelectDialog" />
    <GameNewDialog v-model:dialog="gameNewDialog" />
  </v-app>
</template>

<script>
import ApplicationHeader from './components/ApplicationHeader.vue';
import ConfirmEncounterDeleteDialog from './components/ConfirmEncounterDeleteDialog.vue';
import EncounterNewDialog from './components/EncounterNewDialog.vue';
import GameNewDialog from './components/GameNewDialog.vue';
import GameSelectDialog from './components/GameSelectDialog.vue';
import ThemedActionButton from './components/ThemedActionButton.vue';
import ArcaneAIEmptyState from './components/ArcaneAIEmptyState.vue';
import { mapActions } from 'vuex';

export default {
  components: {
    ApplicationHeader,
    ConfirmEncounterDeleteDialog,
    EncounterNewDialog,
    GameNewDialog,
    GameSelectDialog,
    ThemedActionButton,
    ArcaneAIEmptyState,
  },
  data() {
    return {
      isCompact: false,
      deleteDialogVisible: false,
      deletingEncounterId: '',
      deletingEncounterName: '',
      showEncounterDialog: false,
      gameSelectDialog: false,
      gameNewDialog: false,
    };
  },
  computed: {
    drawerWidth() {
      const width = this.$vuetify.display.width;
      if (width < 1500) {
        return Math.round(width / 4);
      }
      return 300;
    },
    currentGameName() {
      const storeName = this.$store.getters['game/gameName'];
      const routeName = this.$route.params.gameName;

      return storeName || routeName || null;
    },
    recentGames() {
      return this.$store.getters['games/recentGames'] || [];
    },
    encountersList() {
      return this.$store.getters['encounters/encounterNames'] || [];
    },
    roomsList() {
      const all = this.$store.getters['model/allStates'] || [];
      return [...all]
        .filter(s => s && s.name)
        .sort((a, b) => a.name.localeCompare(b.name));
    },
    /**
     * Determines which sidebar group is expanded based on the current route.
     * Single-open: only one section is expanded at a time so the hierarchy stays clear.
     * Routes containing /personality|/welcome|/inventory open Game Setup;
     * /world|/encounter open Maps; /rooms opens Rooms.
     */
    openSections() {
      const path = this.$route.path || '';
      if (/\/(personality|welcome|game-target|help-text|inventory)(\/|$)/.test(path)) return ['setup'];
      if (/\/rooms(\/|$)/.test(path)) return ['rooms'];
      // Default: Maps for /world, /encounter, or anything else
      return ['maps'];
    },
  },
  created() {
    const storedState = localStorage.getItem('drawerCompactState');
    if (storedState !== null) {
      this.isCompact = JSON.parse(storedState);
    }

    window.addEventListener('beforeunload', this.handleBeforeUnload);

    // Initialize Stores
    this.initializeAll();
  },
  beforeUnmount() {
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
  },
  watch: {
    // Watch for route changes to load game when navigating via URL
    '$route.params.gameName': {
      immediate: true,
      async handler(newGameName, oldGameName) {
        // Skip if same game or no game name
        if (!newGameName || newGameName === oldGameName) return;

        // Skip if game is already loaded in store
        const currentStoreGame = this.$store.getters['game/gameName'];
        if (currentStoreGame === newGameName) return;

        // Load the game
        await this.loadGame(newGameName);
        this.$store.dispatch('games/addRecentGame', newGameName);
      }
    }
  },
  methods: {
    ...mapActions('game', {
      initializeGame: 'initialize',
      loadGame: 'loadGame',
    }),
    ...mapActions('games', {
      initializeGames: 'initialize',
    }),
    ...mapActions('sounds', {
      initializeSounds: 'initialize',
    }),

    async initializeAll() {
      await Promise.all([
        this.initializeGame(),
        this.initializeGames(),
        this.initializeSounds()
      ]);

      if (this.$route.params.gameName) {
        await this.loadGame(this.$route.params.gameName);
      }
    },

    toggleDrawerCompact() {
      this.isCompact = !this.isCompact;
      localStorage.setItem('drawerCompactState', JSON.stringify(this.isCompact));
    },
    getEncounterDisplayName(encounterId) {
      const encounter = this.$store.state.encounters?.encounters?.[encounterId];
      return encounter?.name || encounterId;
    },
    getOpenTodosForEncounter(encounterId) {
      const viewId = `encounter_${encounterId}`;
      return this.$store.getters['views/openTodosForView'](viewId) || 0;
    },
    getOpenTodosForWorld() {
      return this.$store.getters['views/openTodosForView']('world') || 0;
    },
    openDeleteDialog(encounterId) {
      this.deletingEncounterId = encounterId;
      this.deletingEncounterName = this.getEncounterDisplayName(encounterId);
      this.deleteDialogVisible = true;
    },
    handleBeforeUnload(event) {
      const hasUnsavedChanges = this.$store.getters['game/hasUnsavedChanges'];
      if (hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = '';
        return '';
      }
    },
    openAddEncounterDialog() {
      this.showEncounterDialog = true;
    },
    async handleSelectRecentGame(gameName) {
      await this.$store.dispatch('games/selectGame', gameName);
      this.$router.push({ name: 'world', params: { gameName } });
    },
    async handleEncounterDelete(encounterId) {
      console.log('[App] handleEncounterDelete START', encounterId);
      try {
        const gameName = this.currentGameName;
        const viewId = `encounter_${encounterId}`;

        console.log('[App] Calling views/deleteView', { gameName, viewId });
        await this.$store.dispatch('views/deleteView', {
          gameName,
          viewId
        });

        console.log('[App] Calling encounters/fetchEncounters', gameName);
        await this.$store.dispatch('encounters/fetchEncounters', gameName);

        if (this.$route.params.encounterId === encounterId) {
          console.log('[App] Current route is deleted encounter, redirecting to world');
          this.$router.replace(`/game/${gameName}/world`);
        }
        console.log('[App] handleEncounterDelete SUCCESS');
      } catch (error) {
        console.error('[App] handleEncounterDelete ERROR:', error);
        // Alert user of failure so it doesn't just "fail silently"
        alert(`Failed to delete encounter: ${error.message || 'Unknown error'}`);
      }
    },
  },
};
</script>

<style>
/* Navigation Drawer — structural layout only, visual styles in theme files */

.nav-drawer__toggle {
  cursor: pointer;
}

.nav-drawer__header--clickable {
  cursor: pointer;
}

.nav-drawer__bullet {
  display: inline-block;
  text-align: center;
}

.nav-drawer__delete-btn {
  opacity: 0;
}

.nav-drawer__subitem:hover .nav-drawer__delete-btn {
  opacity: 1;
}

.nav-drawer__delete-spacer {
  display: inline-block;
}

.nav-drawer__help-disabled {
  opacity: 0.4;
  pointer-events: none;
}

/* Section headers (Game Setup / Maps / Rooms) should not look "active" or "selected"
   even when a child is the current route. Only sub-items show the active indicator. */
.nav-drawer__list :deep(.v-list-group > .v-list-item.v-list-item--active),
.nav-drawer__list :deep(.v-list-group__header.v-list-item--active) {
  background: transparent !important;
  color: inherit !important;
}
.nav-drawer__list :deep(.v-list-group > .v-list-item.v-list-item--active .v-list-item__overlay),
.nav-drawer__list :deep(.v-list-group__header .v-list-item__overlay) {
  opacity: 0 !important;
}
.nav-drawer__list :deep(.v-list-group > .v-list-item.v-list-item--active::before),
.nav-drawer__list :deep(.v-list-group__header.v-list-item--active::before),
.nav-drawer__list :deep(.v-list-group > .v-list-item.v-list-item--active::after),
.nav-drawer__list :deep(.v-list-group__header.v-list-item--active::after) {
  opacity: 0 !important;
}
.nav-drawer__list :deep(.v-list-group > .v-list-item .v-list-item-title) {
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* Sub-items: indented and visually subordinate to the section header */
.nav-drawer__list :deep(.v-list-group__items .v-list-item) {
  padding-inline-start: 32px !important;
  font-size: 0.9rem;
}
.nav-drawer__list :deep(.v-list-group__items .v-list-item-title) {
  font-size: 0.9rem;
  font-weight: 400;
}
</style>

<style scoped>
.content-area {
  height: calc(100vh - var(--v-layout-top));
  overflow: hidden;
}

.content-area :deep(.v-main__wrap) {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
}
</style>
