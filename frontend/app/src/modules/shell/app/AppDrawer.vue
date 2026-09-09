<script setup lang="ts">
import { useAreaVisibilityStore } from '@/modules/core/common/use-area-visibility-store';
import SponsorshipView from '@/modules/premium/SponsorshipView.vue';
import GlobalSearch from '@/modules/shell/components/GlobalSearch.vue';
import NavigationMenu from '@/modules/shell/components/navigation/NavigationMenu.vue';
import RotkiLogo from '@/modules/shell/components/RotkiLogo.vue';

const { isMini, showDrawer } = storeToRefs(useAreaVisibilityStore());
const { isXlAndDown } = useBreakpoint();
const route = useRoute();

watch(route, () => {
  if (get(showDrawer) && get(isXlAndDown))
    set(showDrawer, false);
});

watchImmediate(isXlAndDown, (isXlAndDown) => {
  if (!isXlAndDown) {
    set(showDrawer, true);
  }
});
</script>

<template>
  <RuiNavigationDrawer
    v-model="showDrawer"
    width="300"
    :class-names="{
      content: {
        'flex flex-col border-r border-rui-grey-300 dark:border-rui-grey-800': true,
        '!top-0 !max-h-full': isXlAndDown,
      },
    }"
    :mini-variant="!isXlAndDown"
    :overlay="isXlAndDown"
  >
    <div class="flex-1 overflow-y-auto overflow-x-hidden pb-2">
      <div
        class="flex py-6"
        :class="{
          'px-4': !isMini,
          'px-0 [&>div]:h-8 justify-center': isMini,
        }"
      >
        <RouterLink
          :to="{ name: '/dashboard/' }"
          class="flex items-center gap-3"
        >
          <RotkiLogo
            :text="false"
            :size="isMini ? 1.625 : 2.25"
          />

          <div
            v-if="!isMini"
            class="flex flex-col leading-tight"
          >
            <span class="font-bold text-lg">
              CryptoLedger Gipuzkoa
            </span>
            <span class="text-xs text-rui-text-secondary">
              Entorno de desarrollo
            </span>
          </div>
        </RouterLink>
      </div>

      <GlobalSearch :is-mini="isMini" />
      <NavigationMenu :is-mini="isMini" />
    </div>

    <div
      v-if="!isMini"
      class="px-6 py-3 border-t border-default"
    >
      <SponsorshipView drawer />
    </div>
  </RuiNavigationDrawer>
</template>
