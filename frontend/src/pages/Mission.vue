<template>
	<div class="mission-page chakra">
		<article class="mission-layout wef-1or3k40">
			<aside class="mission-sidebar wef-1uxkxjj">
				<div class="mission-card wef-c9ggn4">
					<h4 class="mission-eyebrow chakra-heading wef-ljorty">About us</h4>
					<div class="mission-nav wef-1nvejj4">
						<nav class="mission-nav-primary wef-cs712m" aria-label="Mission navigation">
							<button
								v-for="section in sections"
								:key="section.id"
								type="button"
								class="mission-link"
								:class="section.id === activeId ? 'wef-19t6g0o is-active' : 'wef-sd1y70'"
								@click="selectSection(section.id)"
								:aria-current="section.id === activeId ? 'true' : undefined"
							>
								{{ section.title }}
							</button>
						</nav>
					</div>
					<div class="mission-related wef-1lx4alh">
						<p class="chakra-text wef-1sdljdm">Related links:</p>
						<p class="chakra-text wef-h8e7xn"><a class="mission-related-link wef-spn4bz" href="/impact">Our impact</a></p>
						<p class="chakra-text wef-h8e7xn"><a class="mission-related-link wef-spn4bz" href="/partners">Partners</a></p>
						<p class="chakra-text wef-h8e7xn"><a class="mission-related-link wef-spn4bz" href="/communities">Communities</a></p>
						<p class="chakra-text wef-h8e7xn"><a class="mission-related-link wef-spn4bz" href="/governance">Governance principles</a></p>
						<p class="chakra-text wef-h8e7xn"><a class="mission-related-link wef-spn4bz" href="/careers">Careers</a></p>
					</div>
				</div>
			</aside>
			<main class="mission-main wef-le0wje">
				<div class="mission-spacer wef-0" aria-hidden="true"></div>
				<h2 class="mission-heading chakra-heading wef-12y4nuq">
					{{ activeSection.title }}
				</h2>
				<div class="mission-content wef-1mdveip">
					<p v-if="activeSection.lead" class="mission-lead" v-html="activeSection.lead"></p>
					<p
						v-for="(paragraph, index) in activeSection.paragraphs"
						:key="`${activeSection.id}-${index}`"
						v-html="paragraph"
					></p>
				</div>
				<div class="mission-back-top wef-bf7em1">
					<button type="button" class="mission-top-btn chakra-button wef-1rmscmr" @click="scrollToTop" aria-label="Back to top">
						<svg viewBox="0 0 21 20" focusable="false" class="chakra-icon wef-blpcuq" aria-hidden="true">
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
import { useRoute, useRouter } from 'vue-router';

const sections = [
	{
		id: 'purpose',
		title: 'Our Mission',
		lead: `<strong>The World Economic Quorum is the global platform for decentralized, transparent, and outcome-driven coordination. It provides a digital, impartial, and not-for-profit ecosystem for stakeholders to align on shared goals, restore trust, and drive measurable progress through collective action.</strong>`,
		paragraphs: [
			'In a world fragmented by systemic failures, the World Economic Quorum unites innovators, entrepreneurs, communities, and leaders from all sectors to shape agile, inclusive, and forward-looking agendas. Founded as a response to the limitations of traditional institutions, it operates independently, free from centralized control or special interests, and upholds the highest standards of transparency and integrity.',
			'At the core of our mission to advance civilization lies a belief in the power of human ingenuity, decentralized innovation, and collaborative systems. We champion a quorum where diverse perspectives converge through open, respectful dialogue, ensuring every voice is amplified and collective intelligence thrives.',
			'This mission is powered by our global community of stakeholders, who unite to identify opportunities and execute solutions for transformative impact. Together, we strive for a thriving world, where trust, innovation, and collective action chart the path to enduring progress.'
		]
	},
	{
		id: 'framework',
		title: 'Operating Framework',
		lead: 'The World Economic Quorum convenes innovators, communities, builders, and leaders across all domains to co-create global, regional, and sectoral strategies. It is decentralized, impartial, free from centralized capture, and upholds the highest standards of transparency, integrity, and collective accountability.',
		paragraphs: [
			'The Quorum’s infrastructure is natively global, leveraging open protocols and interoperable systems to enable borderless participation and coordination. Programs are organized around Digital Commons, Assemblies, and Congresses that translate consensus into executable roadmaps and measurable outcomes.'
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
		lead: 'The Quorum models a new standard of decentralized-yet-structured governance where legitimacy, accountability, transparency, and collective action are the guiding principles.',
		paragraphs: [
			'Ultimate stewardship rests with two principal governors who provide strategic direction while a broader distribution of seats ensures collective accountability. Layered bodies such as the Council of 13, the Council of 33, and the Committee of 300 provide guidance, executive coordination, and domain expertise.',
			'At the broadest tier, the Quorum is powered by an open assembly of contributors who may submit proposals, cast votes, and help steward initiatives—ensuring governance remains participatory and representative.'
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
});

watch(
	() => route.hash,
	(hash) => {
		if (!hash || hash === `#${activeId.value}`) return;
		syncFromHash(hash);
	}
);

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
	padding: 108px 0 0 0;
	color: var(--token-text-dark, #111);
    overflow: auto;
    min-height: calc(100vh - 72px);
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
	position: sticky;
	align-self: flex-start;
	flex: 0 0 280px;
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
	padding: 12px 0 12px 20px;
	text-align: left;
	font-size: 0.98rem;
	font-weight: 600;
	color: #1d2b50;
	border-left: 3px solid transparent;
	cursor: pointer;
	transition: color 0.2s ease, border-color 0.2s ease;
}

.mission-link.is-active {
	color: #0065f2;
	border-color: #0065f2;
}

.mission-link:hover,
.mission-link:focus-visible {
	color: #0065f2;
	border-color: rgba(0, 101, 242, 0.4);
}


.mission-related {
	margin-top: 32px;
	font-size: 0.9rem;
	color: #405078;
}

.mission-related-link {
	color: #0065f2;
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
	border-left: 1px solid #dfe5f0;
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
	margin-top: 48px;
	display: flex;
	justify-content: flex-end;
}

.mission-top-btn {
	background: #f5f8ff;
	border: 1px solid #d6deeb;
	border-radius: 0;
	width: 56px;
	height: 56px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: background 0.2s ease, transform 0.2s ease;
}

.mission-top-btn:hover,
.mission-top-btn:focus-visible {
	background: #e9f1ff;
	transform: translateY(-3px);
}

@media (max-width: 1100px) {
	.mission-layout {
		flex-direction: column;
		gap: 40px;
		padding: 0 28px;
	}
	.mission-sidebar {
		position: static;
		flex: none;
	}
	.mission-main {
		padding-left: 0;
		border-left: 0;
	}
	.mission-nav-primary {
		flex-direction: row;
		flex-wrap: wrap;
		gap: 12px;
	}
	.mission-link {
		padding: 10px 16px;
		border-left: 0;
		border-bottom: 2px solid transparent;
	}
	.mission-link.is-active {
		border-bottom-color: #0065f2;
	}
	.mission-related {
		display: none;
	}
}

@media (max-width: 680px) {
	.mission-layout {
		padding: 0 20px;
	}
	.mission-heading {
		font-size: 1.8rem;
	}
	.mission-top-btn {
		width: 48px;
		height: 48px;
	}
	.mission-back-top {
		justify-content: center;
	}
}
</style>
