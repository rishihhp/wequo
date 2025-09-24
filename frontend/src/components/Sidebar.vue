<template>
  <div>
    <div class="sidebar-overlay" v-if="modelValue" @click="close"></div>
    <aside :class="['sidebar', { open: modelValue }]" role="navigation" aria-label="Main navigation">
      <button class="close-btn" @click="close" aria-label="Close menu" title="Close">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
          <path d="M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M6 18L18 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <nav class="sidebar-nav">
        <a class="sidebar-link" href="#mission" @click="close">Mission</a>
        <a class="sidebar-link" href="#publications" @click="close">Publications</a>
        <a class="sidebar-link" href="#partners" @click="close">Partners</a>
        <a class="sidebar-link" href="#contact" @click="close">Contact Us</a>
      </nav>
    </aside>
  </div>
</template>

<script setup>
import { defineEmits, defineProps, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}

function onKey(e) {
  if (e.key === 'Escape' || e.key === 'Esc') close()
}

// Add/remove global key listener only while sidebar is open
watch(() => props.modelValue, (open) => {
  if (open) document.addEventListener('keydown', onKey)
  else document.removeEventListener('keydown', onKey)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.sidebar-overlay{
  position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:49;
}
.sidebar{
  position:fixed;top:0;left:-320px;width:300px;height:100vh;background:#fff;z-index:50;padding:24px;box-shadow:2px 0 12px rgba(0,0,0,0.12);transition:left .28s ease;
}
.sidebar.open{left:0}
.close-btn{
  color: var(--token-text-dark);
  position: absolute;
  left: 12px;
  top: 6px;
  border: 0;
  background: transparent;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  margin: 0;
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.close-btn:focus{outline: 2px solid var(--token-focus, #2684FF); outline-offset: 2px}
.close-btn:hover{background:rgba(0,0,0,0.06)}
.close-btn:active{background:rgba(0,0,0,0.08)}
.sidebar-nav{display:flex;flex-direction:column;gap:12px;margin-top:36px}
.sidebar-link{color:#111;text-decoration:none;font-weight:600;padding:8px 6px;border-radius:6px}
.sidebar-link:hover{background:var(--token-offwhite)}
</style>
