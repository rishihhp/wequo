<template>
	<div id="main" class="weq-root root-container" style="min-height:100vh;width:auto">
		<header id="hero" class="hero hero-wrap">
			<div class="hero-bg hero-bg-img">
				<img :src="heroImg" alt="hero" />
			</div>
			<div class="hero-content hero-content-inner">
				<p class="eyebrow text-white">International Collective Collaboration</p>
				<h1 class="hero-title hero-title-large"><span>World</span> <span>Economic</span> <span>Quorum</span></h1>
				<h6 class="hero-sub hero-subtext">Bringing together diverse perspectives and expertise to tackle global challenges through collective action.</h6>
				<div class="hero-cta hero-cta-row">
					<a class="btn btn-group btn-primary" href="#contact">Contact Us</a>
					<a class="btn btn-group btn-ghost" href="#publications">See Publications</a>
				</div>
			</div>
		</header>

		<section id="mission" class="section short">
			<div class="flex-container">
				<div class="left">
					<h2>Representing the MAJORITY</h2>
					<p>We unite innovators, leaders, and communities to coordinate practical, outcome-driven solutions to global challenges.</p>
				</div>
				<div class="left">
					<div class="filters">
						<button class="filter active">What</button>
						<button class="filter">Why</button>
						<button class="filter">How</button>
					</div>
					<h3 class="lead">A global, non-profit platform for decentralized collaboration that aligns stakeholders, restores trust, and turns coordination into impact.</h3>
				</div>
			</div>
		</section>

		<section id="publications" class="section publications" ref="pubSectionEl">
			<div class="section-grid">
                <div class="section-flex">
					<div class="left section-text" ref="pubTextEl">
                        <p class="eyebrow">Publications</p>
						<h2>Bringing Coherence to mend a fragmented world</h2>
                        <p>Curated publications offering research, briefings, and actionable recommendations from our community and partners.</p>
                    </div>
                </div>
				<div class="right cards">
					<!-- Card 1: sticky container (slightly shorter like Framer) -->
					<div class="card-container">
						<a class="card" href="./publications/culture-of-civic-responsibility" style="background-color: #000">
							<div class="card-image">
								<img :src="card1" alt="Culture of Civic Responsibility" />
							</div>
							<div class="card-body">
								<h3>Culture of Civic Responsibility</h3>
								<p>Shift global attention toward civic responsibility through transformative narratives based in truth and shared values.</p>
							</div>
						</a>
						</div>

					<!-- Card 2: sticky container -->
					<div class="card-container">
						<a class="card" href="./publications/learning-for-better-futures" style="background-color: #bf9b30">
							<div class="card-image">
								<img :src="card2" alt="Learning for better Futures" />
							</div>
							<div class="card-body">
								<h3>Learning for better Futures</h3>
								<p>Raise learning outcomes at the lowest cost per uplift via AI tutors, teacher upskilling, and vocational fast-tracks.</p>
							</div>
						</a>
					</div>

					<!-- Card 3: sticky container -->
					<div class="card-container">
						<a class="card" href="./publications/health-access-for-all" style="background-color: #844d24">
							<div class="card-image">
								<img :src="card3" alt="Living Healthy Lives" />
							</div>
							<div class="card-body">
								<h3>Living Healthy Lives</h3>
								<p>Expand preventive and primary care via AI triage, clinics-in-a-box, and mental-health coverage.</p>
							</div>
						</a>
					</div>
				</div>
			</div>
		</section>

		<section id="partners" class="section partners">
			<div class="section-grid">
                <div class="section-flex">
                    <div class="left section-text">
                        <h2>Partners</h2>
                        <p>Our ecosystem spans visionary organizations, funds, and initiatives working to reshape culture, technology, governance, and collective intelligence.</p>
                    </div>
                </div>
				<div class="right logos">
					<h2 class="section-title">Selected Partners</h2>
					<div class="logo-grid">
						<!-- Render a 3x2 grid of partner logos. Keep the anchor text/names but add the logo images. -->
						<a v-for="(p, idx) in partners" :key="p.name" :href="p.url" target="_blank" rel="noopener" class="partner">
							<img v-if="p.src" :src="p.src" :alt="p.name" class="partner-logo" />
							<span class="partner-name">{{ p.name }}</span>
						</a>
					</div>
					<div class="company-list">
						<h2 class="section-title">All</h2>
						<div class="companies">
							<a href="https://www.synchronouscity.org/" target="_blank" rel="noopener">Synchronous City</a>
							<a href="https://www.legacyforesight.org/" target="_blank" rel="noopener">Legacy Foresight</a>
							<a href="https://www.freqout.org/" target="_blank" rel="noopener">Freqout</a>
							<a href="https://www.asireadiness.com/landing" target="_blank" rel="noopener">ASI Readiness</a>
							<a href="https://www.creatorcity.org/" target="_blank" rel="noopener">Creator City</a>
							<a href="https://forestcity.org/" target="_blank" rel="noopener">Forest City</a>
							<a href="https://declarationofai.org/" target="_blank" rel="noopener">Declaration Of AI</a>
							<a href="https://uranus.org/" target="_blank" rel="noopener">Uranus</a>
							<a href="https://secreteservice.com/" target="_blank" rel="noopener">Secrete Service</a>
							<a href="https://omegateam.org/" target="_blank" rel="noopener">Omega Team</a>
							<a href="https://aiccelerator.org/" target="_blank" rel="noopener">Aiccelerator</a>
							<a href="https://lasthumansleft.com/" target="_blank" rel="noopener">Last Humans Left</a>
							<a href="https://www.percival.vc/" target="_blank" rel="noopener">Percival</a>
							<a href="http://prodemic.org/" target="_blank" rel="noopener">Prodemic</a>
							<a href="https://spearritual.com/" target="_blank" rel="noopener">Spear Ritual</a>
							<a href="https://4rf.org/" target="_blank" rel="noopener">4rf</a>
							<a href="https://www.dnacellerator.com/" target="_blank" rel="noopener">DNAcellerator</a>
							<a href="https://web3socialfund.com/" target="_blank" rel="noopener">Web3 Social Fund</a>
						</div>
					</div>
				</div>
			</div>
		</section>

		<section id="work" class="section short">
			<div class="flex-container">
				<h2>Shaping the global vibe</h2>
				<h4>Culture is infrastructure. We commission work that moves norms, not just news.</h4>
			</div>
		</section>

		<section id="contact" class="section contact">
			<div class="contact-grid">
				<div class="left pos-relative">
					<h1>Contact</h1>
					<p>We welcome dialogue from councils, operators, media, and partners. Whether you are exploring membership, proposing a mandate, submitting an operator dossier, or simply seeking clarity about our work, we encourage you to reach out.</p>
				</div>
				<div class="right">
					<form @submit.prevent="submitForm" class="contact-form">
						<label class="label-name">
							<div class="form-text-input form-input-wrapper">
								<input class="form-input" v-model="form.name" type="text" placeholder="Your Name" required />
							</div>
						</label>
						<div class="two-cols row-gap-30">
							<label class="label-email">
								<div class="form-text-input form-input-wrapper">
									<input class="form-input" v-model="form.email" type="email" placeholder="E-Mail" required />
								</div>
							</label>
							<label class="label-phone">
								<div class="form-text-input form-input-wrapper">
									<input class="form-input" v-model="form.phone" type="tel" placeholder="Phone" required />
								</div>
							</label>
						</div>
						<label class="label-message">
							<div class="form-text-input form-input-wrapper">
								<textarea class="form-input" v-model="form.message" placeholder="Your message" required></textarea>
							</div>
						</label>
						<button type="submit" class="btn btn-primary">Submit</button>
						<p v-if="sent" class="sent">Thanks — we received your message.</p>
						<p v-if="error" class="error">{{ error }}</p>
					</form>
				</div>
			</div>
		</section>

		<footer class="footer">
			<div class="container footer-inner">
				<div>© 2025 World Economic Quorum</div>
				<div>Made by <a href="https://anterportfolio.framer.website/" target="_blank">Mohamed Anter</a> at Persist Ventures</div>
			</div>
		</footer>
	</div>
</template>

<script setup>
import { reactive, ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import heroImg from '../assets/GWlxgrH9lo91CE3UMYEiWcdMVsM.png';
import card1 from '../assets/LghU1ToVACojn81DkgMO6S2Dlg4.png';
import card2 from '../assets/2qTb7a0TGpF3zVwt3pmEbInH40.png';
import card3 from '../assets/C4wQP6LejcIeET5hC6YedS3tWHs.png';

// Dynamically import partner logos from assets/partners
const partnerFiles = import.meta.glob('../assets/partners/*.{png,jpg,jpeg,svg}', { eager: true, as: 'url' });

// helper to normalize filename -> key
function baseName(path) {
	return path.replace(/^.*[\\/]/, '');
}

// Map filenames to partner entries (name and url)
const partnersMeta = [
	{ file: 'Persist_Ventures.png', name: 'Persist Ventures', url: 'https://persistventures.com/' },
	{ file: 'DIA.png', name: 'DIA', url: 'https://dia.wiki/' },
	{ file: 'Federal_Preserve.png', name: 'Federal Preserve', url: 'https://federalpreserve.org/' },
	{ file: 'solarpunkism.png', name: 'solarpunkism', url: 'https://www.solarpunkism.com/' },
	{ file: 'Faithism.png', name: 'Faithism', url: 'https://www.faithism.net/' },
	{ file: 'Purple_Rock.png', name: 'Purple Rock', url: 'https://www.purplerock.xyz/' },
];

const partners = partnersMeta.map((m) => {
	// find matching import by filename
	const matchKey = Object.keys(partnerFiles).find((k) => baseName(k) === m.file) || null;
	const src = matchKey ? partnerFiles[matchKey] : null;
	return { name: m.name, url: m.url, src };
});

const form = reactive({ name: '', email: '', phone: '', message: '' });
const sent = ref(false);
const error = ref('');
// sidebarOpen is managed by App.vue

// Dynamic sticky offset for publications cards: topnav height + section-text height
const pubSectionEl = ref(null);
const pubTextEl = ref(null);
let resizeObs;

function computeStickyTop() {
	const root = document.documentElement;
	const nav = document.querySelector('.topnav-fixed');
	const navH = nav ? nav.getBoundingClientRect().height : parseFloat(getComputedStyle(root).getPropertyValue('--nav-height')) || 72;
	const textEl = pubTextEl.value || document.querySelector('.publications .section-text');
	const textH = textEl ? textEl.getBoundingClientRect().height : 0;
	const top = Math.max(0, Math.round(navH + textH));
	root.style.setProperty('--pub-sticky-top', `${top}px`);
}

onMounted(async () => {
	await nextTick();
	computeStickyTop();
	resizeObs = new ResizeObserver(() => computeStickyTop());
	if (pubTextEl.value) resizeObs.observe(pubTextEl.value);
	const nav = document.querySelector('.topnav-fixed');
	if (nav) resizeObs.observe(nav);
	window.addEventListener('resize', computeStickyTop);
});

onBeforeUnmount(() => {
	if (resizeObs) resizeObs.disconnect();
	window.removeEventListener('resize', computeStickyTop);
});

async function submitForm() {
	error.value = '';
	sent.value = false;
	try {
		// For now just simulate submit — user can wire to an API endpoint later.
		await new Promise((r) => setTimeout(r, 600));
		sent.value = true;
		// reset form
		form.name = form.email = form.phone = form.message = '';
	} catch (e) {
		error.value = 'Failed to submit';
	}
}

</script>

<!-- styles moved to TopNav.vue -->

<style scoped>
.logo-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 18px;
	align-items: center;
}
.logo-grid .partner {
	display: flex;
	flex-direction: column;
	align-items: center;
	text-decoration: none;
	color: inherit;
	padding: 18px;
}
.partner-logo {
	width: 100%;
	max-width: 154px;
	max-height: 154px;
	object-fit: contain;
	background: var(--token-bg-light);
	padding: 12px;
    transition: transform .36s ease;
}
.partner-logo:hover {
    transform: scale(1.18);
}
.partner-name {
	margin-top: 8px;
	font-size: 13px;
	text-align: center;
}

@media (max-width: 777px) {
    .section-grid {
        flex-direction: column;
    }
    .section-flex {
        position: sticky;
        top: 72px;
    }
	.logo-grid { grid-template-columns: repeat(2, 1fr); }

}

/* Publications cards — mimic Framer look */
.publications .cards {
	display: flex;
	flex-direction: column;
	gap: 0; /* no gap between cards */
}

.publications .card-container {
	position: sticky;
	top: 72px;
	width: 100%;
	height: 50vh; /* like Framer yj9404/aoety1 */
	z-index: 1;
	margin: 0; /* remove any vertical margins */
}


.publications .card {
	display: block;
	position: relative;
	width: 100%;
	height: 100%;
	border-radius: 0; /* square edges */
	padding: 0; /* no internal padding that can create visual gaps */
	overflow: hidden;
	text-decoration: none;
	color: #fff;
	box-shadow: 0 0.72px 2.28px -1.21px rgba(0,0,0,0.18), 0 2.28px 18.5px -3.6px rgba(0,0,0,0.18), 0 6px 36px -3.6px rgba(0,0,0,0.06);
	transition: transform .72s ease, box-shadow .28s ease, opacity .28s ease;
}
.publications .card img {
    transition: transform .72s ease;
}
.publications .card:hover {
	box-shadow: 0 1px 3px -1px rgba(0,0,0,0.24), 0 3px 12px -2px rgba(0,0,0,0.20), 0 16px 46px -4px rgba(0,0,0,0.14);
}
.publications .card:hover img {
    transform: scale(1.05);
}

.publications .card-image {
	position: absolute;
	inset: 0;
	z-index: 0;
}

.publications .card-image img {
	display: block;
	width: 100%;
	height: 100%;
	object-fit: cover;
	object-position: center;
}

.publications .card::after {
	/* Bottom gradient overlay like Framer to ensure text readability */
	content: "";
	position: absolute;
	inset: 0;
	background: linear-gradient(to bottom, rgba(0,0,0,0) 40%, rgba(0,0,0,.6) 75%, rgba(0,0,0,.85) 100%);
	z-index: 1;
	pointer-events: none;
}

.publications .card-body {
	position: absolute;
	left: 0;
	right: 0;
	bottom: 0;
	padding: 24px;
	display: flex;
	flex-direction: column;
	gap: 8px;
	z-index: 2; /* above gradient */
}

.publications .card h3 {
	margin: 0;
	font-weight: 600;
	font-family: "Mluvka", system-ui, sans-serif;
	font-size: clamp(18px, 2.2vw, 28px);
	line-height: 1.15;
}

.publications .card p {
	margin: 0;
	font-family: "Mluvka", system-ui, sans-serif;
	font-size: clamp(14px, 1.6vw, 16px);
	line-height: 1.35;
}

@media (max-width: 777px) {
	.publications .card-container { height: 40vh; top: var(--pub-sticky-top, 72px); }
	.publications .card-body { padding: 18px; }
}

</style>
