<script setup lang="ts">
defineProps<{ messages?: string[] }>()
</script>

<template>
  <ul v-if="messages?.length" class="errors" role="alert">
    <li v-for="message in messages" :key="message">{{ message }}</li>
  </ul>
</template>
