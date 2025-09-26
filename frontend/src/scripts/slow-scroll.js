// Lightweight slow-scroll module
// - Smooth-scrolls to anchor links using a configurable duration and easing
// - Adds basic wheel smoothing by intercepting wheel events and animating scroll
// Usage: import './scripts/slow-scroll.js' in your entrypoint

(function () {
  if (typeof window === 'undefined') return

  const DEFAULT_DURATION = 666 // ms for anchor jumps
  const WHEEL_SMOOTHING = true
  const WHEEL_SENSITIVITY = 0.72 // multiplier for wheel delta
  const WHEEL_DURATION = 420 // ms for wheel-driven incremental scroll

  // easing function (easeOutCubic)
  function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3) }

  // animate from current scrollTop to target over duration
  function animateScroll(targetY, duration = DEFAULT_DURATION) {
    const startY = window.scrollY || window.pageYOffset
    const start = performance.now()
    const maxScroll = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight) - window.innerHeight
    const clampedTarget = Math.max(0, Math.min(maxScroll, targetY))
    if (Math.abs(clampedTarget - startY) < 1) return Promise.resolve()

    return new Promise((resolve) => {
      function frame(now) {
        const elapsed = now - start
        const t = Math.min(1, elapsed / duration)
        const eased = easeOutCubic(t)
        window.scrollTo(0, Math.round(startY + (clampedTarget - startY) * eased))
        if (t < 1) requestAnimationFrame(frame)
        else resolve()
      }
      requestAnimationFrame(frame)
    })
  }

  // Intercept anchor clicks
  function handleAnchorClicks(e) {
    // find nearest anchor with href starting with '#'
    const a = e.target.closest('a[href^="#"]')
    if (!a) return
    const href = a.getAttribute('href')
    if (!href || href === '#') return
    const id = href.slice(1)
    const targetEl = document.getElementById(id)
    if (!targetEl) return

    e.preventDefault()
    const rect = targetEl.getBoundingClientRect()
    const targetY = window.scrollY + rect.top
    animateScroll(targetY).then(() => {
      // update hash without jumping
      history.pushState && history.pushState(null, '', href)
    })
  }

  // Wheel smoothing: velocity + RAF loop for smooth, cancellable scrolling
  function setupWheelSmoothing() {
    if (!WHEEL_SMOOTHING) return

    // Tunables
    let velocity = 0
    const MAX_VELOCITY = 72
    const FRICTION = 0.666 // per frame multiplier (closer to 1 => longer glide)
    const MIN_VELOCITY = 0.1

    let rafId = null
    let lastTime = 0

    function step(now) {
      if (!lastTime) lastTime = now
      const dt = Math.min(36, now - lastTime) / 18.5 // approx frames; protect large dt
      lastTime = now

      if (Math.abs(velocity) > MIN_VELOCITY) {
        // integrate velocity into scroll position
        const current = window.scrollY || window.pageYOffset
        const next = current + velocity * dt
        const maxScroll = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight) - window.innerHeight
        const clamped = Math.max(0, Math.min(maxScroll, next))
        // if clamped hit boundary, damp velocity
        if (clamped === 0 || clamped === maxScroll) velocity *= 0.06
        window.scrollTo(0, Math.round(clamped))
        // apply friction
        velocity *= Math.pow(FRICTION, dt)
        rafId = requestAnimationFrame(step)
      } else {
        // stop animation
        velocity = 0
        rafId = null
        lastTime = 0
      }
    }

    function onWheel(e) {
      // ignore if ctrl/meta pressed (zooming)
      if (e.ctrlKey || e.metaKey) return
      // Prevent native scroll so our animation controls motion
      e.preventDefault()

      // Accumulate wheel into velocity; scale by sensitivity
      velocity += e.deltaY * WHEEL_SENSITIVITY
      // clamp to reasonable range
      velocity = Math.max(-MAX_VELOCITY, Math.min(MAX_VELOCITY, velocity))

      // start RAF loop if not running
      if (!rafId) rafId = requestAnimationFrame(step)
    }

    // Passive option removal to allow preventDefault
    window.addEventListener('wheel', onWheel, { passive: false })

    // cleanup
    window.addEventListener('beforeunload', () => {
      if (rafId) cancelAnimationFrame(rafId)
    })
  }

  // init on DOMContentLoaded or right away if ready
  function init() {
    document.addEventListener('click', handleAnchorClicks)
    setupWheelSmoothing()
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init)
  else init()

  // expose for runtime tuning
  window.__wequo_slow_scroll = {
    animateScroll,
    setDuration(ms) { DEFAULT_DURATION = ms },
  }
})()
