<template>
  <div class="login-page-container">
    <div class="content">
      <div class="card card-container">
        <div class="card-body">
          <h2 class="text-center mb-5">
            Do I know you&nbsp;?
          </h2>

          <div v-if="!!error">
            <div class="alert alert-warning">
              {{ error }}
            </div>
          </div>

          <b-form @submit.prevent="postLogin">
            <b-form-group>
              <b-input-group class="mb-2 mr-sm-2 mb-sm-0">
                <b-form-input id="email" v-model="email" type="email" placeholder="Email" required />
              </b-input-group>
            </b-form-group>

            <b-form-group>
              <b-input-group class="mb-2 mr-sm-2 mb-sm-0">
                <b-form-input id="password" v-model="password" type="password" placeholder="Password" required />
              </b-input-group>
            </b-form-group>

            <b-form-group>
              <b-row>
                <b-col>
                  <b-spinner v-if="loading" variant="primary" small />
                  <b-button v-if="!loading" type="submit" variant="primary">
                    Login
                  </b-button>
                </b-col>
                <b-col class="text-right">
                  <a href="#">Forgot password ?</a>
                </b-col>
              </b-row>
            </b-form-group>
          </b-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

export default {
  layout: 'login',
  data () {
    return {
      email: null,
      password: null,
      callbackRoute: '/',
    };
  },
  computed: {
    loading () {
      return this.$store.getters['auth/loading'];
    },
    error () {
      return this.$store.getters['auth/error'];
    },
  },
  mounted () {
    this.routeCallback = this.$route.query.callback || '/';
  },
  methods: {
    async postLogin () {
      if (await this.$store.dispatch('auth/login', { email: this.email, password: this.password })) {
        this.$router.push({ name: 'index' });
      }
    },
  },
};
</script>

<style lang="scss">
.login-page-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  background-image: url('/img/background1.jpg');
  background-size: cover;
  background-position: center;

  .content {
    width: 90%;
    max-width: 576px;

    .card-container {
      padding: 30px 20px;
      color: $grey_lighter;
      background-color: $grey_darker;
    }
  }
}
</style>
