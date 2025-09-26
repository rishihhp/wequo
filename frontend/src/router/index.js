import { createRouter, createWebHistory } from 'vue-router';

const routes = [
	{
		path: '/',
		name: 'home',
		component: () => import('../components/Home.vue'),
		meta: { title: 'World Economic Quorum', hero: true }
	},
	{
		path: '/mission',
		name: 'mission',
		component: () => import('../pages/Mission.vue'),
		meta: { title: 'Mission | World Economic Quorum', hero: false }
	}
];

const router = createRouter({
	history: createWebHistory(),
	routes,
	scrollBehavior(to, from, savedPosition) {
		if (savedPosition) return savedPosition;
		if (to.hash) {
			return { el: to.hash, behavior: 'smooth' };
		}
		return { top: 0 };
	}
});

router.afterEach((to) => {
	if (typeof document !== 'undefined') {
		document.title = to.meta?.title || 'World Economic Quorum';
	}
	// If the route contains a hash (anchor), dispatch a custom event so
	// our slow-scroll module can animate to the target after the SPA updates
	// the DOM. Use a short timeout to allow components to mount/layout.
	if (to.hash) {
		try {
			setTimeout(() => {
				const detail = { hash: to.hash };
				// Dispatch as CustomEvent on window so scripts can listen.
				const ev = new CustomEvent('wequo:navigate', { detail });
				window.dispatchEvent(ev);
			}, 40);
		} catch (e) {
			// defensive: ignore if CustomEvent or window not available
		}
	}
});

export default router;
