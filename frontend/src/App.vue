<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import Home from './components/Home.vue';
import TopNav from './components/TopNav.vue';
import Sidebar from './components/Sidebar.vue';

const sidebarOpen = ref(false);

function onScroll() {
	// toggle when user has scrolled past 100vh
	if (typeof window === 'undefined' || typeof document === 'undefined') return;
	if (window.scrollY < window.innerHeight) document.body.classList.add('hero-visible');
	else document.body.classList.remove('hero-visible');
}

onMounted(() => {
	// init state
	onScroll();
	window.addEventListener('scroll', onScroll, { passive: true });
});

onUnmounted(() => {
	window.removeEventListener('scroll', onScroll);
});
</script>

<template>
	<TopNav v-model="sidebarOpen" />
	<Sidebar v-model="sidebarOpen" />
	<Home />
</template>

<style scoped>
/* App-level styles can remain minimal; global styles are in style.css */
</style>