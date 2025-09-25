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

		<section id="mission" class="section mission">
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

		<section id="publications" class="section publications">
			<div class="flex-container publications-grid">
				<div class="left">
					<p class="eyebrow">Publications</p>
					<h3>Research, Reports & Essays</h3>
					<p>Curated publications offering research, briefings, and actionable recommendations from our community and partners.</p>
				</div>
				<div class="right cards">
					<a class="card" href="./publications/culture-storytelling-for-civic-strength" style="background-color: #000">
						<img :src="card1" alt="Culture & Storytelling" />
						<h3>Culture & Storytelling</h3>
						<p>Shift global attention toward truth, coherence, and civic strength through canonical works, broadcast rituals, and durable memetics.</p>
					</a>
					<a class="card" href="./publications/learning-for-better-futures" style="background-color: #bf9b30">
						<img :src="card2" alt="Learning" />
						<h3>Learning for better Futures</h3>
						<p>Raise learning outcomes at the lowest cost per uplift via AI tutors, teacher upskilling, and vocational fast-tracks.</p>
					</a>
					<a class="card" href="./publications/health-access-for-all" style="background-color: #844d24">
						<img :src="card3" alt="Health" />
						<h3>Living Healthy Lives</h3>
						<p>Expand preventive and primary care via AI triage, clinics-in-a-box, and mental-health coverage.</p>
					</a>
				</div>
			</div>
		</section>

		<section id="partners" class="section partners">
			<div class="flex-container">
				<div class="left">
					<h3>Partners</h3>
					<p>Our ecosystem spans visionary organizations, funds, and initiatives working to reshape culture, technology, governance, and collective intelligence.</p>
				</div>
				<div class="right logos">
					<h4>Selected Partners</h4>
					<div class="logo-grid">
						<a href="https://persistventures.com/" target="_blank" rel="noopener">Persist Ventures</a>
						<a href="https://dia.wiki/" target="_blank" rel="noopener">DIA</a>
						<a href="https://federalpreserve.org/" target="_blank" rel="noopener">Federal Preserve</a>
						<a href="https://www.solarpunkism.com/" target="_blank" rel="noopener">solarpunkism</a>
						<a href="https://www.faithism.net/" target="_blank" rel="noopener">Faithism</a>
						<a href="https://www.purplerock.xyz/" target="_blank" rel="noopener">Purple Rock</a>
					</div>
					<div class="company-list">
						<h4>All</h4>
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

		<section id="work" class="section work">
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
import { reactive, ref } from 'vue';
import heroImg from '../assets/GWlxgrH9lo91CE3UMYEiWcdMVsM.png';
import card1 from '../assets/LghU1ToVACojn81DkgMO6S2Dlg4.png';
import card2 from '../assets/2qTb7a0TGpF3zVwt3pmEbInH40.png';
import card3 from '../assets/C4wQP6LejcIeET5hC6YedS3tWHs.png';

const form = reactive({ name: '', email: '', phone: '', message: '' });
const sent = ref(false);
const error = ref('');
// sidebarOpen is managed by App.vue

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
