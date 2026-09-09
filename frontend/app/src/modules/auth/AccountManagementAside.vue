<script lang="ts" setup>
defineSlots<{
  default: () => any;
}>();
</script>

<template>
  <div class="max-w-[31rem] mx-auto lg:max-w-[29%] flex-col grow-0 lg:flex-1 border-b lg:border-b-0 border-default lg:border-l h-full relative overflow-auto hidden lg:flex justify-between">
    <div class="p-6 lg:px-8 lg:py-12 xl:p-12 flex-1 overflow-auto">
      <slot />
    </div>
  </div>
</template>
