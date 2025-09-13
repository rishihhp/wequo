<template>
  <div class="dashboard">
    <h1>Data Dashboard</h1>
    <div v-if="loading">Loading...</div>
    <div v-if="error">{{ error }}</div>
    <div v-if="summary">
      <label for="package-select"><strong>Select package:</strong></label>
      <select id="package-select" v-model="selectedPackage" @change="fetchSummary">
        <option v-for="p in packages" :key="p.date" :value="p.date">{{ p.date }}</option>
      </select>

      <h2>Package: {{ selectedPackage }}</h2>
      <p v-if="summary.timestamp">Generated at: {{ new Date(summary.timestamp).toLocaleString() }}</p>
      <p v-else>Generated at: unknown</p>
      
      <div class="stats-grid">
        <div class="stat-card">
          <h3>Summary Stats</h3>
          <p><strong>Total Series:</strong> {{ summary.analytics?.summary_stats?.total_series ?? 0 }}</p>
          <p><strong>Total Data Points:</strong> {{ summary.analytics?.summary_stats?.total_data_points ?? 0 }}</p>
          <p><strong>Sources:</strong> {{ (summary.analytics?.summary_stats?.sources ?? []).join(', ') }}</p>
        </div>

        <div class="stat-card" v-if="(summary.analytics?.top_deltas ?? []).length">
          <h3>Top Deltas</h3>
          <ul>
            <li v-for="delta in summary.analytics.top_deltas" :key="delta.series_id">
              <strong>{{ delta.series_id }}:</strong> {{ (delta.delta_pct * 100).toFixed(1) }}%
            </li>
          </ul>
        </div>

        <div class="stat-card" v-if="(summary.analytics?.anomalies ?? []).length">
          <h3>Anomalies</h3>
          <ul>
            <li v-for="anomaly in summary.analytics.anomalies" :key="anomaly.series_id">
              <strong>{{ anomaly.series_id }}:</strong> {{ anomaly.value.toFixed(2) }} (z-score: {{ anomaly.z_score.toFixed(2) }})
            </li>
          </ul>
        </div>
      </div>
      
      <div ref="chart" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, onBeforeUnmount } from 'vue';
import * as d3 from 'd3';

// API base can be provided via Vite env variable VITE_API_BASE or falls back to page origin
const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE)
  ? import.meta.env.VITE_API_BASE
  : `${window.location.protocol}//${window.location.host}`;
// Common local backend fallback for development when Vite is serving the frontend
const DEFAULT_BACKEND = 'http://127.0.0.1:5000';

async function fetchWithFallback(path) {
  const bases = [API_BASE, DEFAULT_BACKEND];
  let lastErr = null;
  for (const base of bases) {
    try {
      const url = `${base.replace(/\/$/, '')}${path}`;
      const res = await fetch(url);
      if (!res.ok) {
        const text = await res.text().catch(() => '<unable to read body>');
        const snippet = text.slice(0, 500);
        throw new Error(`Failed to fetch ${url}: ${res.status} ${res.statusText}. Snippet: ${snippet}`);
      }
      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        const text = await res.text().catch(() => '');
        const snippet = text.slice(0, 500);
        throw new Error(`Expected JSON from ${url} but got '${contentType}'. Snippet: ${snippet}`);
      }
      try {
        const data = await res.json();
        // Success
        return data;
      } catch (parseErr) {
        const text = await res.text().catch(() => '');
        const snippet = text.slice(0, 500);
        throw new Error(`Failed to parse JSON from ${url}: ${parseErr.message}. Snippet: ${snippet}`);
      }
    } catch (err) {
      // remember and try next base
      lastErr = err;
      console.warn(`fetchWithFallback failed for base ${base}:`, err.message);
      continue;
    }
  }
  throw lastErr || new Error('Unknown fetch error');
}

const loading = ref(true);
const error = ref(null);
const summary = ref(null);
const packages = ref([]);
const selectedPackage = ref(null);
const chart = ref(null);
let resizeObserver = null;

onMounted(async () => {
  try {
    const pkgs = await fetchWithFallback('/api/packages');

    if (!Array.isArray(pkgs) || pkgs.length === 0) {
      throw new Error('No data packages found.');
    }

    packages.value = pkgs;
    selectedPackage.value = pkgs[0].date;

    await fetchSummary();

    // Resize observer to redraw chart on container resize
    if (chart.value && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => {
        drawChart();
      });
      resizeObserver.observe(chart.value);
    }

  } catch (e) {
    error.value = e.message;
    console.error(e);
  } finally {
    loading.value = false;
  }
});

onBeforeUnmount(() => {
  if (resizeObserver && chart.value) resizeObserver.unobserve(chart.value);
});

watch(selectedPackage, async (newVal, oldVal) => {
  if (newVal && newVal !== oldVal) {
    await fetchSummary();
  }
});

async function fetchSummary() {
  if (!selectedPackage.value) return;
  loading.value = true;
  error.value = null;
  try {
  summary.value = await fetchWithFallback(`/api/package/${selectedPackage.value}/summary`);

    await nextTick();
    drawChart();
  } catch (e) {
    error.value = e.message || String(e);
    console.error(e);
  } finally {
    loading.value = false;
  }
}

function clearChart() {
  if (!chart.value) return;
  d3.select(chart.value).selectAll('*').remove();
}

function drawChart() {
  clearChart();
  if (!summary.value || !Array.isArray(summary.value.analytics?.top_deltas) || summary.value.analytics.top_deltas.length === 0) return;

  const data = summary.value.analytics.top_deltas.slice();
  // Ensure numeric values
  data.forEach(d => { d.delta_pct = Number(d.delta_pct) || 0; });

  const container = d3.select(chart.value);
  const bounds = chart.value.getBoundingClientRect();
  const margin = { top: 20, right: 30, bottom: 40, left: 140 };
  const width = Math.max(300, bounds.width) - margin.left - margin.right;
  const height = Math.max(200, data.length * 30) - margin.top - margin.bottom;

  const svg = container.append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  // x domain should cover negative and positive
  const minVal = d3.min(data, d => d.delta_pct) ?? 0;
  const maxVal = d3.max(data, d => d.delta_pct) ?? 0;
  const x = d3.scaleLinear()
    .domain([Math.min(0, minVal), Math.max(0, maxVal)])
    .range([0, width]);

  const y = d3.scaleBand()
    .range([0, height])
    .domain(data.map(d => d.series_id))
    .padding(0.15);

  // Axis
  svg.append('g')
    .attr('class', 'y-axis')
    .call(d3.axisLeft(y));

  svg.append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).ticks(5).tickFormat(d3.format('.0%')));

  // zero line
  const zeroX = x(0);
  svg.append('line')
    .attr('x1', zeroX)
    .attr('x2', zeroX)
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', '#444')
    .attr('stroke-dasharray', '2,2');

  // bars: handle negative and positive
  svg.selectAll('.bar')
    .data(data)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('y', d => y(d.series_id))
    .attr('height', y.bandwidth())
    .attr('x', d => x(Math.min(0, d.delta_pct)))
    .attr('width', d => Math.abs(x(d.delta_pct) - x(0)))
    .attr('fill', d => d.delta_pct >= 0 ? '#2ca02c' : '#d62728');

  // value labels
  svg.selectAll('.label')
    .data(data)
    .enter()
    .append('text')
    .attr('class', 'label')
    .attr('y', d => (y(d.series_id) || 0) + y.bandwidth() / 2)
    .attr('x', d => d.delta_pct >= 0 ? x(d.delta_pct) + 6 : x(d.delta_pct) - 6)
    .attr('dy', '0.35em')
    .attr('text-anchor', d => d.delta_pct >= 0 ? 'start' : 'end')
    .text(d => (d.delta_pct * 100).toFixed(1) + '%');
}
</script>

<style scoped>
.dashboard {
  font-family: system-ui, Avenir, Helvetica, Arial, sans-serif;
  color: #333;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}
.stat-card {
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
}
.stat-card h3 {
  margin-top: 0;
}
ul {
  padding-left: 20px;
}
</style>
