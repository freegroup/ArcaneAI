<template>
  <div class="label-with-help">
    <label>
      <slot />
    </label>
    <HelpButton v-if="helpText" @click="showHelp = true" />
    <ExtendedHelpDialog
      v-if="helpText"
      v-model="showHelp"
      :title="helpTitle || String($slots.default?.()[0]?.children || '')"
      :helpText="helpText"
    />
  </div>
</template>

<script>
import HelpButton from './HelpButton.vue'
import ExtendedHelpDialog from './ExtendedHelpDialog.vue'

export default {
  name: 'PropertyLabel',
  components: { HelpButton, ExtendedHelpDialog },
  props: {
    helpText: { type: String, default: '' },
    helpTitle: { type: String, default: '' }
  },
  data() {
    return { showHelp: false }
  }
}
</script>

<style scoped>
.label-with-help {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}
.label-with-help label {
  margin: 0;
}
</style>
