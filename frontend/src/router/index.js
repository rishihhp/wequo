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
});

export default router;
