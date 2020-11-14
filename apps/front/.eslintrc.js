module.exports = {
  root: true,
  env: {
    browser: true,
    node: true
  },
  parserOptions: {
    parser: 'babel-eslint'
  },
  extends: [
    '@nuxtjs',
    'plugin:nuxt/recommended'
  ],
  // add your custom rules here
  rules: {
    "comma-dangle": [2, "always-multiline"],
    "semi": [2, "always"],
    "vue/multiline-html-element-content-newline": ["off"]
  }
}
