<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import { useRoute, RouterView } from 'vue-router';
import TopNav from './components/TopNav.vue';
import Sidebar from './components/Sidebar.vue';

const sidebarOpen = ref(false);
const route = useRoute();

const transitionName = computed(() => route.meta?.transition || 'fade');

function hasHeroSection() {
	return route.meta?.hero === true;
}

function onScroll() {
	// toggle when user has scrolled past 100vh
	if (typeof window === 'undefined' || typeof document === 'undefined') return;
	if (!hasHeroSection()) {
		document.body.classList.remove('hero-visible');
		return;
	}
	if (window.scrollY < window.innerHeight - 72) document.body.classList.add('hero-visible');
	else document.body.classList.remove('hero-visible');
}

function enableHeroListeners() {
	onScroll();
	window.addEventListener('scroll', onScroll, { passive: true });
}

function disableHeroListeners() {
	window.removeEventListener('scroll', onScroll);
	document.body.classList.remove('hero-visible');
}

onMounted(() => {
	if (hasHeroSection()) enableHeroListeners();
});

watch(
	() => hasHeroSection(),
	(hasHero) => {
		disableHeroListeners();
		if (hasHero) enableHeroListeners();
	},
	{ flush: 'post' }
);

onUnmounted(() => {
	disableHeroListeners();
});
</script>

<template>
	<TopNav v-model="sidebarOpen" />
	<Sidebar v-model="sidebarOpen" />
	<transition
		:name="transitionName"
		:mode="'out-in'"
		>
		<RouterView :key="$route.path" />
	</transition>
</template>

<style scoped>
/* Route transition styles: default fade plus optional slide-left/slide-right */
.fade-enter-active,
.fade-leave-active {
	transition: opacity 216ms ease;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}

.slide-left-enter-active,
.slide-left-leave-active {
	transition: transform 216ms cubic-bezier(.2,.9,.2,1), opacity 216ms ease;
}
.slide-left-enter-from {
	transform: translateX(6%);
	opacity: 0;
}
.slide-left-leave-to {
	transform: translateX(-6%);
	opacity: 0;
}

.slide-right-enter-active,
.slide-right-leave-active {
	transition: transform 216ms cubic-bezier(.2,.9,.2,1), opacity 216ms ease;
}
.slide-right-enter-from {
	transform: translateX(-6%);
	opacity: 0;
}
.slide-right-leave-to {
	transform: translateX(6%);
	opacity: 0;
}

/* App-level styles can remain minimal; global styles are in style.css */
</style>