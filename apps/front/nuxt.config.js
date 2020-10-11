import dotenv from 'dotenv';

// Load base ENV variables
dotenv.config({ path: '../../.env' });
// Load app ENV variables
dotenv.config();

export default {
  ssr: false,
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
 css: [
  '@/assets/css/colors.scss',
  '@/assets/css/main.scss',
],
  /*
  ** Router
   */
  router: {},
  /*
  ** Plugins to load before mounting the App
  */
  plugins: [
    '~/plugins/ui',
    '~/plugins/api',
    '~/plugins/local-storage',
    '~/plugins/geocoding',
    '~/plugins/google-maps',
  ],
  /*
  ** Environment variables
   */
  env: {
    API_URL: process.env.API_URL,
    GMAP_API_KEY: process.env.GMAP_API_KEY,
  },
  /*
  ** Nuxt.js dev-modules
  */
  buildModules: [
    // Doc: https://github.com/nuxt-community/eslint-module
    '@nuxtjs/eslint-module',
    // https://github.com/nuxt-community/style-resources-module
    '@nuxtjs/style-resources',
  ],
  /*
  ** Nuxt.js modules
  */
  modules: [
    [
      // Doc: https://bootstrap-vue.js.org
      'bootstrap-vue/nuxt',
      {
        icons: true, // Install the IconsPlugin (in addition to BootStrapVue plugin)
      },
    ],
  ],
  /*
   ** Style resources
   */
  styleResources: {
    scss: ['~/assets/css/*.scss'],
  },
  /*
  ** Build configuration
  */
  build: {
    /*
    ** You can extend webpack config here
    */
    extend (config) {
      config.resolve.alias['vue'] = 'vue/dist/vue.common';
    }
  },
};
