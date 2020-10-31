<template>
  <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" viewBox="0 0 100 125" :width="width">
    <path :fill="color" d="M86.775,48.146L86.775,48.146v-8.108h-8.191v-8.375h-8.201l-0.001-8.017h8.183v-8.201h-8.201v8.201h-8.183  v8.201H37.773v-8.201h-8.182v-8.201H21.39v8.201h8.182l-0.001,8.017H21.37v8.375h-8.192v8.108l0,0H4.977V72.75h8.201V56.347h0.001  h8.191V72.75h8.179v8.2h0.042h16.359v-8.2H29.591h-0.02v-8.202h0.001h40.81h0.001v8.202h-0.02h-16.36v8.2h16.36h0.042v-8.2h8.179  V56.347h8.191l0,0V72.75h8.201V48.146H86.775z M37.745,48.146h-8.163v-8.099h8.163V48.146z M70.371,48.146H62.21v-8.099h8.161  V48.146z" />
  </svg>
</template>

<script>
export default {
  props: {
    width: {
      type: Number,
      default: 20,
    },
    color: {
      type: String,
      default: '#000',
    },
  },
};
</script>
