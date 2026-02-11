// vue.config.js
const { defineConfig } = require('@vue/cli-service');
const webpack = require('webpack');
const MonacoWebpackPlugin = require('monaco-editor-webpack-plugin');

module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    plugins: [
      new webpack.DefinePlugin({
        __VUE_OPTIONS_API__: true,
        __VUE_PROD_DEVTOOLS__: false,
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false,
      }),
      new MonacoWebpackPlugin({
        languages: ['html', 'css', 'javascript', 'json'],
        features: ['!gotoSymbol'], // Disable features we don't need
      }),
    ],
  },
});