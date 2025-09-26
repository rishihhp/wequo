// Lightweight slow-scroll module
// - Smooth-scrolls to anchor links using a configurable duration and easing
// - Adds improved wheel smoothing: velocity + spring/damper with time-based integration
// Usage: import './scripts/slow-scroll.js' in your entrypoint

(function () {
  if (typeof window === 'undefined') return

  let DEFAULT_DURATION = 666 // ms for anchor jumps
  const WHEEL_SMOOTHING = true

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
    const a = e.target.closest && e.target.closest('a[href^="#"]')
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

  function init() {
    document.addEventListener('click', handleAnchorClicks)
    setupWheelSmoothing()

    // Support SPA route changes: animate to top when history changes or when
    // an app dispatches a 'wequo:navigate' custom event with { hash }.
    window.addEventListener('popstate', () => {
      // small delay to allow new content to layout
      setTimeout(() => animateScroll(0, 420), 33)
    })

    window.addEventListener('wequo:navigate', (ev) => {
      // allow callers to pass { top: number } in detail, default to 0
      const top = ev && ev.detail && typeof ev.detail.top === 'number' ? ev.detail.top : 0
      setTimeout(() => animateScroll(top, 420), 33)
    })
  }

  // Wheel smoothing: target + physics-based spring/damper integrator
  function setupWheelSmoothing() {
    if (!WHEEL_SMOOTHING) return

    // Tunables (exposed below)
    let sensitivity = 1.0 // multiplier for wheel delta in pixels
    let stiffness = 0.01 // spring coefficient
    let damping = 0.18 // damping coefficient
    let mass = 1.0 // mass for physics integration
    const STOP_THRESHOLD = 0.06 // when to stop RAF loop

    // internal state
    let target = window.scrollY || window.pageYOffset
    let current = target
    let velocity = 0
    let rafId = null
    let lastTime = 0

    function maxScroll() {
      return Math.max(document.documentElement.scrollHeight, document.body.scrollHeight) - window.innerHeight
    }

    function clamp(v) {
      const m = maxScroll()
      return Math.max(0, Math.min(m, v))
    }

    // Normalize wheel delta to pixels for consistent behavior across devices
    function normalizeDelta(e) {
      let delta = e.deltaY
      // deltaMode: 0=pixel, 1=line, 2=page
      if (e.deltaMode === 1) delta *= 18
      else if (e.deltaMode === 2) delta *= window.innerHeight
      return delta
    }

    function step(now) {
      if (!lastTime) lastTime = now
      const dt = Math.min(36, now - lastTime) / 18.5 // approx frames; protect large dt
      lastTime = now

      // physics: spring force toward target
      const diff = target - current
      const spring = stiffness * diff
      const dampingForce = -damping * velocity
      const accel = (spring + dampingForce) / mass

      velocity += accel * dt
      current += velocity * dt

      // clamp and handle boundaries
      const clamped = clamp(current)
      if (clamped !== current) {
        current = clamped
        velocity = 0
        target = clamp(target)
      }

      // apply the scroll position (round for integer pixel positions)
      window.scrollTo(0, Math.round(current))

      // stop if motion has settled
      if (Math.abs(velocity) < STOP_THRESHOLD && Math.abs(diff) < 0.6) {
        velocity = 0
        rafId = null
        lastTime = 0
        return
      }

      rafId = requestAnimationFrame(step)
    }

    function onWheel(e) {
      // ignore if ctrl/meta pressed (zooming)
      if (e.ctrlKey || e.metaKey) return

      // don't intercept when a form control or contenteditable is focused
      try {
        const active = document.activeElement
        if (active) {
          const tag = (active.tagName || '').toLowerCase()
          if (tag === 'input' || tag === 'textarea' || active.isContentEditable) return
        }
      } catch (err) {
        // defensive - if accessing activeElement throws, fall through
      }

      // Prevent native scroll so our animation controls motion
      e.preventDefault()

      const delta = normalizeDelta(e) * sensitivity
      // accumulate into target; this gives natural high-resolution touchpad feel
      target = clamp(target + delta)

      // kick off RAF loop
      if (!rafId) rafId = requestAnimationFrame(step)
    }

    // Cancel smooth motion when user interacts directly (pointer, keyboard, touch)
    function cancelMotion() {
      if (rafId) {
        cancelAnimationFrame(rafId)
        rafId = null
      }
      current = window.scrollY || window.pageYOffset
      target = current
      velocity = 0
      lastTime = 0
    }

    // Passive option removal to allow preventDefault
    window.addEventListener('wheel', onWheel, { passive: false })
    window.addEventListener('touchstart', cancelMotion, { passive: true })
    window.addEventListener('pointerdown', cancelMotion, { passive: true })
    window.addEventListener('keydown', (ev) => {
      // arrow keys/page keys should cancel our motion so native behavior works
      const keys = ['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' ']
      if (keys.includes(ev.key)) cancelMotion()
    })

    window.addEventListener('beforeunload', () => {
      if (rafId) cancelAnimationFrame(rafId)
    })

    // Expose tuning knobs for runtime adjustments
    window.__wequo_slow_scroll = window.__wequo_slow_scroll || {}
    Object.assign(window.__wequo_slow_scroll, {
      // tuning
      setSensitivity(s) { if (typeof s === 'number') sensitivity = s },
      setStiffness(s) { if (typeof s === 'number') stiffness = s },
      setDamping(d) { if (typeof d === 'number') damping = d },
      setMass(m) { if (typeof m === 'number') mass = m },
      // control
      enable() { /* no-op: always enabled by default */ },
      disable() { /* to disable, we'd remove listeners - not implemented */ },
      // helper to jump to a position immediately (cancels motion)
      jumpTo(y) {
        cancelMotion()
        const cl = clamp(y)
        window.scrollTo(0, Math.round(cl))
        current = target = cl
      }
    })
  }

  // Ensure programmatic scrolling (animateScroll) and wheel-smoothing share state.
  // Wrap the outer `animateScroll` so it cancels any ongoing wheel physics motion
  // and keeps the internal `current/target` in sync before and after the animation.
  // This prevents the two systems from fighting and causing jumps.
  if (typeof animateScroll === 'function') {
    const _originalAnimate = animateScroll
    animateScroll = function (targetY, duration = DEFAULT_DURATION) {
      try {
        // If wheel smoothing is enabled and running, cancel and sync to current browser position
        if (typeof cancelMotion === 'function') cancelMotion()
      } catch (e) {
        // defensive
      }
      // Read the runtime scroll position and initialise the wheel-smoothing state
      try {
        const startY = window.scrollY || window.pageYOffset
        // If the wheel smoothing closure created `current`/`target`, set them if available
        if (typeof window.__wequo_slow_scroll !== 'undefined') {
          // attempt best-effort sync via exposed jumpTo if available
          if (window.__wequo_slow_scroll && typeof window.__wequo_slow_scroll.jumpTo === 'function') {
            // jumpTo cancels motion and sets internal current/target
            window.__wequo_slow_scroll.jumpTo(startY)
          }
        }
      } catch (err) {
        // ignore
      }

      // Run the original animate; when it finishes, sync any remaining smoothing state
      return _originalAnimate(targetY, duration).then(() => {
        try {
          const clamped = Math.max(0, Math.min(Math.max(document.documentElement.scrollHeight, document.body.scrollHeight) - window.innerHeight, window.scrollY || window.pageYOffset))
          if (window.__wequo_slow_scroll && typeof window.__wequo_slow_scroll.jumpTo === 'function') {
            window.__wequo_slow_scroll.jumpTo(clamped)
          }
        } catch (e) {
          // ignore
        }
      })
    }
  }

  // init on DOMContentLoaded or right away if ready
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init)
  else init()

  // preserve animateScroll helper on global if another script wants it
  window.__wequo_slow_scroll = window.__wequo_slow_scroll || {}
  Object.assign(window.__wequo_slow_scroll, {
    animateScroll,
    setDuration(ms) {
      if (typeof ms === 'number' && ms >= 0) DEFAULT_DURATION = ms
    },
    navigateToTop(top = 0, delay = 10) {
      setTimeout(() => animateScroll(top, DEFAULT_DURATION), delay)
    }
  })
})()
