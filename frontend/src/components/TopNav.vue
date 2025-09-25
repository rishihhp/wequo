<template>
  <div class="topnav">
    <nav class="nav-container topnav-fixed nav-center">
      <div class="nav-inner">
        <div class="nav-left">
          <button class="hamburger" @click="$emit('update:modelValue', !props.modelValue)" aria-label="Toggle menu">
            <span class="bar"></span>
            <span class="bar"></span>
            <span class="bar"></span>
          </button>
        </div>
        <div class="nav-center-logo">
          <a class="logo logo-wrap" href="./">
            <div class="logo-wrap">
              <img :src="logo" alt="WEQ logo" />
            </div>
          </a>
        </div>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
const props = defineProps({ modelValue: Boolean });
import logo from '../assets/logo.png';
</script>

<style scoped>
/* Header adjustments for centered logo and hamburger */
.nav-inner{display:flex;align-items:center;justify-content:space-between}
.nav-left{display:flex;align-items:center}
.nav-center-logo{position:absolute;left:50%;transform:translateX(-50%)}
.hamburger{display:inline-flex;flex-direction:column;gap:4px;padding:8px;border-radius:8px;border:0;background:transparent;cursor:pointer; height: 42px; width: 42px; align-items: center; justify-content: center;}
.hamburger .bar{width:22px;height:2px;background:var(--token-text-dark);display:block}
/* No outline when active/focused; but keep accessible focus styles via background */
.hamburger:focus{outline:none}
.hamburger:active{outline:none}

/* hover background: opaque when hovered; color adapts to hero visibility */
.hamburger{transition:background .18s ease, opacity .18s ease}
.topnav .hamburger:hover{background:rgba(0,0,0,0.08)}
body.hero-visible .topnav .hamburger:hover{background:rgba(255,255,255,0.12)}

/* Ensure topnav has relative positioning so absolute center works */
.topnav .nav-inner{position:relative}

/* small screens: hide logo left spacing and ensure hamburger visible */
@media (max-width:809.98px){
	.nav-items{display:none}
}
</style>

<style>
/* Invert the logo when the page is NOT in hero-visible state. */
.logo-wrap img { transition: filter 200ms ease, opacity 200ms ease; }
body.hero-visible .logo-wrap img { filter: none; }
body:not(.hero-visible) .logo-wrap img { filter: invert(1); }

/* Hamburger color: white when hero visible, dark otherwise */
.topnav .hamburger .bar { background: var(--token-text-dark); }
body.hero-visible .topnav .hamburger .bar { background: var(--token-white); }
</style>
