<template>
  <div class="toolbar">
    <div class="toolbar-item" :style="{ fontSize: '30px' }" @click="$emit('add-invader')">
      <b-icon icon="plus" />
    </div>

    <div class="toolbar-item" @click="$emit('geolocate')">
      <b-icon icon="geo-alt-fill" />
    </div>
  </div>
</template>

<script>
export default {

};
</script>

<style lang="scss" scoped>
.toolbar-item {
  text-align: center;
  width: 30px;
  height: 30px;
  font-size: 20px;
  line-height: 24px;
  background-color: $grey_darker;
  border-radius: 5px;
  margin: 0 0 5px 0;
  padding: 0;
  cursor: pointer;
}
</style>
