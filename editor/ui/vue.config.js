// vue.config.js
const { defineConfig } = require('@vue/cli-service');
const webpack = require('webpack');

module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    plugins: [
      new webpack.DefinePlugin({ // Add 'new' before DefinePlugin
        __VUE_OPTIONS_API__: true,               // Enable Options API
        __VUE_PROD_DEVTOOLS__: false,            // Disable devtools in production
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false, // Disable hydration mismatch details
      }),
    ],
  },
});
