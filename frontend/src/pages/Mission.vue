<template>
	<div class="mission-page chakra" ref="pageRoot">
		<article class="mission-layout 0">
			<aside class="mission-sidebar j">
				<div class="mission-card">
					<h4 class="mission-eyebrow chakra-heading">About us</h4>
					<div class="mission-nav 4">
						<nav class="mission-nav-primary" aria-label="Mission navigation">
							<button
								v-for="section in sections"
								:key="section.id"
								type="button"
								class="mission-link"
								:class="section.id === activeId ? 'is-active' : ''"
								@click="selectSection(section.id)"
								:aria-current="section.id === activeId ? 'true' : undefined"
							>
								{{ section.title }}
							</button>
						</nav>
					</div>
					<div class="mission-related h">
						<p class="chakra-text m">Related links:</p>
						<p class="chakra-text"><a class="mission-related-link" href="/impact">Our impact</a></p>
						<p class="chakra-text"><a class="mission-related-link" href="/partners">Partners</a></p>
						<p class="chakra-text"><a class="mission-related-link" href="/communities">Communities</a></p>
						<p class="chakra-text"><a class="mission-related-link" href="/governance">Governance principles</a></p>
						<p class="chakra-text"><a class="mission-related-link" href="/careers">Careers</a></p>
					</div>
				</div>
			</aside>
			<main class="mission-main">
				<div class="mission-spacer" a-hidden="true"></div>
				<transition name="fade" mode="out-in">
					<section :key="activeSection.id">
						<h2 class="mission-heading chakra-heading q">
							{{ activeSection.title }}
						</h2>
						<div class="mission-content p">
							<p v-if="activeSection.lead" class="mission-lead" v-html="activeSection.lead"></p>
							<p
								v-for="(paragraph, index) in activeSection.paragraphs"
								:key="`${activeSection.id}-${index}`"
								v-html="paragraph"
							></p>
						</div>
					</section>
				</transition>
				<div class="mission-back-top" v-if="showBackTop">
					<button type="button" class="mission-top-btn chakra-button r" @click="scrollToTop" aria-label="Back to top">
						<svg viewBox="-1 1 22 22" focusable="false" class="chakra-icon" aria-hidden="true">
							<path fill-rule="evenodd" clip-rule="evenodd" d="M16.1364 12.3863C15.7849 12.7378 15.2151 12.7378 14.8636 12.3863L10.5 8.02269L6.13642 12.3863C5.78495 12.7378 5.2151 12.7378 4.86363 12.3863C4.51216 12.0348 4.51216 11.465 4.86363 11.1135L9.86363 6.1135C10.0324 5.94472 10.2613 5.8499 10.5 5.8499C10.7387 5.8499 10.9676 5.94472 11.1364 6.1135L16.1364 11.1135C16.4879 11.465 16.4879 12.0348 16.1364 12.3863Z" fill="#0065F2" />
						</svg>
					</button>
				</div>
			</main>
		</article>
	</div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { nextTick, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const sections = [
	{
		id: 'purpose',
		title: 'Our Mission',
		lead: `<strong>The World Economic Quorum is the global platform for decentralized, transparent, and outcome-driven coordination. It provides a digital, impartial, and not-for-profit ecosystem for stakeholders to align on shared goals, restore trust, and drive measurable progress through collective action.</strong>`,
		paragraphs: [
			'In a world fragmented by systemic failures, the World Economic Quorum unites innovators, entrepreneurs, communities, and leaders from all sectors to shape agile, inclusive, and forward-looking agendas. Founded as a response to the limitations of traditional institutions, it operates independently, free from centralized control or special interests, and upholds the highest standards of transparency and integrity.',
			'At the core of our mission to advance civilization lies a belief in the power of human ingenuity, decentralized innovation, and collaborative systems. We champion a quorum where diverse perspectives converge through open, respectful dialogue, ensuring every voice is amplified and collective intelligence thrives.',
			'This mission is powered by our global community of stakeholders, who unite to identify opportunities and execute solutions for transformative impact. Together, we strive for a thriving world, where trust, innovation, and collective action chart the path to enduring progress. The World Economic Quorum aims to provide a clear way forward for our evolving civilization, redefining global coordination beyond the constraints of traditional institutions.',
		]
	},
	{
		id: 'framework',
		title: 'Operating Framework',
		lead: 'The World Economic Quorum convenes innovators, communities, builders, and leaders across all domains to co-create global, regional, and sectoral strategies. It is decentralized, impartial, free from centralized capture, and upholds the highest standards of transparency, integrity, and collective accountability.',
		paragraphs: [
			"Unlike legacy institutions bound by geography, the Quorum exists as a distributed digital network with nodes across the world. Its infrastructure is natively global, leveraging open protocols and interoperable systems to enable borderless participation, collaboration, and trust.",
			"Founded as a response to the shortcomings of hierarchical governance, the Quorum operates as a living ecosystem—continuously evolving to meet the demands of an interconnected, rapidly changing world. It engages stakeholders through open dialogue, decentralized governance, and binding commitments to action, enabling societies to become more adaptive, resilient, inclusive, and future-ready.",
			"<strong>Digital Commons</strong><br> The Quorum’s work is accelerated by Digital Commons and open systems where communities of purpose align with ambitious goals through competitive cooperation. We architect systems and incentives necessary to address planetary-scale challenges, coordinating resources and collective intelligence. Guided by community consensus, we transform ambition into executable action through transparent roadmaps, iterative projects, and open knowledge generation.",
			"<strong>Assemblies and Congresses</strong><br> The work of the Commons is amplified through Assemblies and Congresses where stakeholders convene to deliberate, decide, and commit to shared objectives. These gatherings are designed to foster inclusive dialogue, harness collective intelligence, and catalyze coordinated action. Assemblies focus on specific themes or sectors, while Congresses bring together a broader spectrum of voices to address overarching challenges and opportunities.",
			"<strong>Impact</strong><br> We build trust through transparency, empower decision making through open data and analytics, and accelerate execution through decentralized coordination. Our efforts include trust pacts forged between historically opposed communities, open intelligence reports mapping systemic risks and opportunities, and hundreds of distributed initiatives designed to elevate human prosperity, restore ecological balance, foster diplomacy beyond borders, and steward the governance of transformative technologies."
		]
	},
	{
		id: 'stewardship',
		title: 'Stewardship',
		lead: 'The Quorum’s stewardship is a covenant between contributors, leaders, and the community — a recognition that the Quorum exists to serve civilization beyond any single lifetime or agenda. Stewardship is exercised through layered councils and committees that safeguard mission and integrity.',
		paragraphs: [
			'At its highest level, stewardship rests with principal governors who safeguard balance and ensure alignment with the founding mission. Councils and committees act as custodians of the Quorum’s integrity, reputation, and purpose.',
			'True stewardship is measured by accountability and service. Members are expected to think beyond personal interest, protecting the Quorum’s values and contributing to its long-term health.'
		]
	},
	{
		id: 'origin',
		title: 'Origins',
		lead: 'The World Economic Quorum began as a grassroots movement born from a shared vision between entrepreneurs, system designers, and movement builders who saw the need for a new model of coordination and governance.',
		paragraphs: [
			'WEQ emerged as a direct response to systemic failures: financial systems unable to provide resilience, governance structures unable to adapt, and institutions unable to restore trust. It was built not to reform the old order, but to create a lasting alternative ecosystem transparently driven by collective action.'
		]
	},
	{
		id: 'governance',
		title: 'Leadership & Governance',
		lead: 'The World Economic Quorum models a new standard of decentralized-yet-structured governance, where legitimacy, accountability, transparency, and collective action are the guiding principles. Rather than concentrating power, stewardship is distributed across layered councils and assemblies, ensuring both agility and resilience in decision-making.',
		paragraphs: [
			'The Quorum is guided by two Principal Governors, who provide strategic direction and act as custodians of mission and values. Surrounding them are tiered councils that balance leadership with accountability. The Council of 13—comprised of the highest contributors—serves as guardians of the Quorum’s integrity and long-term vision, with members earning their place through demonstrable impact and contribution.',
			'The Council of 33 functions as the Quorum’s executive body, coordinating initiatives, setting priorities, and translating collective ambition into actionable outcomes. In parallel, the Committee of 300 draws on deep domain expertise across regions and disciplines, channeling specialized knowledge to ensure decisions are informed, adaptive, and forward-looking.',
			'Beyond these councils, governance extends to an Executive Assembly of 144,000 open seats, reserved for the most dedicated contributors across the community. This Assembly is the participatory backbone of the Quorum—members propose initiatives, share input, and cast binding votes, ensuring governance remains representative and merit-based.',
			'At the broadest tier, the Quorum is powered by an open global assembly of contributors whose collaborative intelligence drives innovation and whose collective actions shape the trajectory of civilization. Authority is earned, ranked by contribution, and continuously renewed through open participation.',
			'Together, this living governance structure ensures the Quorum remains transparent, accountable, and oriented toward advancing humanity through trust, cooperation, and collective purpose.'
		]
	},
	{
		id: 'policies',
		title: 'Code of Conduct',
		lead: 'The World Economic Quorum adheres to principles of Transparency, Decentralization, Integrity, Respect, and Collective Excellence. These principles guide every action, decision, and contribution.',
		paragraphs: [
			'Members must apply these principles in every action and uphold the Quorum’s reputation through accountability, respectful collaboration, and civic responsibility.',
			'Participation requires adherence to conflict-of-interest disclosures, transparent funding sources, and shared safety protocols. Membership is ranked by contribution and each action contributes to the integrity of the Quorum.'
		]
	}
];

const route = useRoute();
const router = useRouter();

const activeId = ref(sections[0].id);
const pageRoot = ref(null)
const showBackTop = ref(false)

const activeSection = computed(() => sections.find((section) => section.id === activeId.value) ?? sections[0]);

function syncFromHash(hash) {
	if (!hash) return;
	const normalized = hash.replace(/^#/, '');
	if (sections.some((section) => section.id === normalized)) {
		activeId.value = normalized;
	}
}

function selectSection(id) {
	if (id === activeId.value) return;
	if (!sections.some((section) => section.id === id)) return;
	activeId.value = id;
	const targetHash = `#${id}`;
	if (route.hash !== targetHash) {
		router.replace({ hash: targetHash }).catch(() => {});
	}
}

onMounted(() => {
	if (route.hash) {
		syncFromHash(route.hash);
	}
	// determine initial visibility and install observers
	const updateVisibility = () => {
		try {
			const el = pageRoot.value || document.querySelector('.mission-page')
			if (!el) return
			showBackTop.value = (el.scrollHeight || el.offsetHeight) > (window.innerHeight || document.documentElement.clientHeight)
		} catch (e) {
			// defensive
		}
	}

	// ResizeObserver for content changes
	let ro = null
	try {
		ro = new ResizeObserver(() => updateVisibility())
		if (pageRoot.value) ro.observe(pageRoot.value)
		else {
			const el = document.querySelector('.mission-page')
			if (el) ro.observe(el)
		}
	} catch (e) {
		ro = null
	}

	// window resize should also update
	window.addEventListener('resize', updateVisibility)

	// update after mount and whenever activeSection changes (transition)
	nextTick(() => updateVisibility())

	onUnmounted(() => {
		if (ro && pageRoot.value) ro.unobserve(pageRoot.value)
		window.removeEventListener('resize', updateVisibility)
	})
});

watch(
	() => route.hash,
	(hash) => {
		if (!hash || hash === `#${activeId.value}`) return;
		syncFromHash(hash);
	}
);

// When the active section changes, wait for the DOM update (transition will run)
watch(activeSection, async () => {
	await nextTick()
	// allow the transition a frame to update layout, then recompute visibility
	try {
		const el = pageRoot.value || document.querySelector('.mission-page')
		if (el) showBackTop.value = (el.scrollHeight || el.offsetHeight) > (window.innerHeight || document.documentElement.clientHeight)
	} catch (e) {
		// ignore
	}
})

function scrollToTop() {
	if (typeof window === 'undefined') return;
	// Use the shared slow-scroll API so wheel smoothing and scripted scrolls stay in sync
	if (window.__wequo_slow_scroll && typeof window.__wequo_slow_scroll.navigateToTop === 'function') {
		window.__wequo_slow_scroll.navigateToTop(0, 10)
		return
	}
	window.scrollTo({ top: 0, behavior: 'smooth' });
}
</script>

<style scoped>
.mission-page {
	background: #ffffff;
	padding: 108px 0;
	color: var(--token-text-dark, #111);
    min-height: calc(100vh);
}

.mission-layout {
	max-width: 1240px;
	margin: 0 auto;
	display: flex;
	align-items: flex-start;
	gap: 72px;
	padding: 0 40px;
}

.mission-sidebar {
	/* Keep sidebar in a stable stacking context and ensure sticky works */
	position: sticky;
	top: 108px;
	z-index: 5;
	align-self: flex-start;
	flex: 0 0 280px;
	/* Prevent the sidebar from becoming affected by overflow on ancestor elements */
	-webkit-backface-visibility: hidden;
	backface-visibility: hidden;
}

.mission-card {
	padding: 0;
	background: transparent;
	box-shadow: none;
	border-radius: 0;
}

.mission-eyebrow {
	font-size: 0.85rem;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	margin-bottom: 16px;
	color: #0b1f40;
}

.mission-nav-primary {
	display: flex;
	flex-direction: column;
	gap: 6px;
}

.mission-link {
	background: transparent;
	border: 0;
	padding: 12px 0 12px 18px;
	text-align: left;
	font-size: 0.98rem;
	font-weight: 600;
	color: #1d2b50;
	border-left: 3px solid transparent;
	cursor: pointer;
	transition: all 0.18s ease;
}

.mission-link:hover,
.mission-link:focus-visible {
	color: var(--active-color);
	border-color: var(--active-color);
	opacity: 0.72;
}

.mission-link.is-active {
	color: #0063FA;
	border-color: #0063FA;
	opacity: 1;
	padding-left: 36px;
}

.mission-related {
	margin-top: 32px;
	font-size: 0.9rem;
	color: var(--token-text-dark);
}

.mission-related-link {
	color: var(--token-text-dark);
	text-decoration: none;
	font-weight: 500;
}

.mission-related-link:hover,
.mission-related-link:focus-visible {
	text-decoration: underline;
}

.mission-main {
	flex: 1;
	padding-left: 56px;
	border-left: 1px solid var(--token-off-white, #f3f3f3);
}

.mission-heading {
	font-size: clamp(2rem, 3vw, 2.6rem);
	margin-bottom: 28px;
	color: #0b1f40;
}

.mission-content {
	display: flex;
	flex-direction: column;
	gap: 18px;
	max-width: 760px;
}

.mission-lead {
	font-size: 1.12rem;
	line-height: 1.75;
	font-weight: 600;
	color: #11254a;
}

.mission-content p {
	margin: 0;
	font-size: 1.02rem;
	line-height: 1.7;
	color: #1f2f52;
}

.mission-content p strong {
	color: #0b1f40;
}

.mission-back-top {
	margin: 36px auto;
	display: flex;
	justify-content: center;
}

.mission-top-btn {
	background: var(--token-white);
	border: 1px solid var(--token-off-white, #f3f3f3);
	box-shadow: 0 3px 6px rgba(0, 0, 0, 0.06);
	border-radius: 0;
	width: 54px;
	height: 54px;
	border-radius: 50%;
	display: grid;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: background 0.216s ease, transform 0.216s ease;
}

/* Make the SVG/icon inside the button slightly larger (requested 40x40) */
.mission-top-btn svg,
.mission-top-btn .chakra-icon {
	width: 36px;
	height: 36px;
}

.mission-top-btn:hover,
.mission-top-btn:focus-visible {
	background: var(--token-off-white);
	transform: translateY(-3px);
}

@media (max-width: 1100px) {
	.mission-layout {
		flex-direction: column;
		gap: 36px;
		padding: 0 18px;
	}
	.mission-sidebar {
		position: static;
		flex: none;
		width: -webkit-fill-available;
	}
	.mission-main {
		padding-left: 0;
		border-left: 0;
	}
	.mission-nav-primary {
		flex-direction: column;
		flex-wrap: wrap;
	}
	.mission-link {
		padding: 6px 18px;
		border-left: 0;
		border-left: 3px solid transparent;
	}
	.mission-link.is-active {
		border-left-color: var(--active-color);
	}
	.mission-related {
		display: none;
	}
	.mission-eyebrow {
		margin-left: 18px;
	}
}

@media (max-width: 690px) {
	.mission-layout {
		padding: 0 18px;
	}
	.mission-heading {
		font-size: 1.8rem;
	}
	.mission-back-top {
		justify-content: center;
	}
}

/* Fade transition for mission main content (0.216s ease) */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 216ms cubic-bezier(.4,0,.2,1);
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
.fade-enter-to,
.fade-leave-from {
    opacity: 1;
}
</style>
