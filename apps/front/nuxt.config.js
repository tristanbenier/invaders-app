import dotenv from 'dotenv';

// Load base ENV variables
dotenv.config({ path: '../../.env' });
// Load app ENV variables
dotenv.config();

export default {
  mode: 'spa',
  server: {},
  /*
  ** Headers of the page
  */
  head: {
    title: 'Invaders',
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { hid: 'description', name: 'description', content: process.env.npm_package_description || '' },
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
    ],
  },
  /*
  ** Customize the progress-bar color
  */
  loading: { color: '#003366' },
  /*
  ** Global CSS
  */
  css: [],
  /*
  ** Router
   */
  router: {},
  /*,
  ** Plugins to load before mounting the App
  */
  plugins: [],
  /*
  ** Environment variables
   */
  env: {},
  /*
  ** Nuxt.js dev-modules
  */
  buildModules: [
    // Doc: https://github.com/nuxt-community/eslint-module
    '@nuxtjs/eslint-module',
  ],
  /*
  ** Nuxt.js modules
  */
  modules: [
    // Doc: https://bootstrap-vue.js.org
    'bootstrap-vue/nuxt',
  ],
  /*
   ** Bootstrap Vue
   */
  bootstrapVue: {
    icons: true, // Install the IconsPlugin (in addition to BootStrapVue plugin
  },
  /*
  ** Build configuration
  */
  build: {
    /*
    ** You can extend webpack config here
    */
    extend (config, ctx) {
    },
  },
};
