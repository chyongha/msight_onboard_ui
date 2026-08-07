// Synthesizes an alarm beep with the Web Audio API instead of playing an
// audio file — msight_original_script/realtime_plot.py's FCW.wav asset
// was never actually available in this repo, and this avoids needing a
// new Flask route + a committed audio file just to make a warning sound.
//
// Browsers block audio from playing until a user gesture happens on the
// page (autoplay policy) — same reason the original script needed an
// explicit "Enable voice alarm" button rather than just always playing
// sound. AudioContext has the identical restriction, so this needs the
// same opt-in toggle.
import { ref, watch, onBeforeUnmount } from 'vue'

const BEEP_FREQUENCY_HZ = 880 // A5 — attention-getting, not painful
const BEEP_DURATION_S = 0.15  // each individual beep lasts 150ms
const BEEP_INTERVAL_MS = 500  // a new beep starts every 500ms while the alarm is active
const BEEP_GAIN = 0.15        // volume, 0 (silent) to 1 (full) — quiet-ish; this is a UI demo, not a real siren

// isWarningRef: a ref passed IN from the caller (WarningBanner.vue), so
// this composable can react to it without needing to know where it
// actually comes from.
export function useVoiceAlarm(isWarningRef) {
  const soundEnabled = ref(false)        // has the user clicked "Enable voice alarm"?
  const soundBlockedMessage = ref('')    // set if the browser refused to let audio play

  let audioCtx = null   // the Web Audio API context — created lazily (see ensureContext), not up front
  let beepTimer = null  // the id of the repeating setInterval() driving the beeps, or null if not currently beeping

  function ensureContext() {
    // Only create the AudioContext the first time it's actually needed —
    // some browsers start it in a "suspended" state until a user gesture
    // resumes it anyway, so there's no benefit to creating it earlier.
    if (!audioCtx) {
      const Ctor = window.AudioContext || window.webkitAudioContext  // webkitAudioContext = old Safari's prefixed name for the same API
      audioCtx = new Ctor()
    }
    return audioCtx
  }

  function playBeep() {
    const ctx = ensureContext()
    const osc = ctx.createOscillator()   // generates the actual tone
    const gain = ctx.createGain()        // controls its volume
    osc.type = 'square'                  // waveform shape — square = harsher/more attention-grabbing than the default sine wave
    osc.frequency.value = BEEP_FREQUENCY_HZ
    gain.gain.setValueAtTime(BEEP_GAIN, ctx.currentTime)
    osc.connect(gain)              // wire the oscillator's output into the gain (volume) node...
    gain.connect(ctx.destination)  // ...and the gain node into the speakers
    osc.start()
    osc.stop(ctx.currentTime + BEEP_DURATION_S)  // schedule it to stop automatically after BEEP_DURATION_S seconds
  }

  function startAlarm() {
    if (beepTimer !== null) return  // already beeping — don't stack a second interval on top
    playBeep()                       // play one immediately, don't wait for the first interval tick
    beepTimer = setInterval(playBeep, BEEP_INTERVAL_MS)
  }

  function stopAlarm() {
    if (beepTimer !== null) {
      clearInterval(beepTimer)
      beepTimer = null
    }
  }

  function toggleSound() {
    soundEnabled.value = !soundEnabled.value

    if (!soundEnabled.value) {
      // user just turned it off — stop immediately, nothing else to do
      stopAlarm()
      return
    }

    // The user-gesture requirement is satisfied right here (this only
    // runs from a click handler), so resume() should succeed. If it
    // doesn't, surface why instead of silently doing nothing.
    ensureContext().resume()  // resume() is a Promise — AudioContext can start "suspended" and needs this call to actually allow sound
      .then(() => {
        soundBlockedMessage.value = ''
        if (isWarningRef.value) startAlarm()  // if a warning is ALREADY active when sound gets enabled, start beeping right away
      })
      .catch(() => {
        soundBlockedMessage.value = 'Voice alarm blocked until user interaction'
      })
  }

  // Runs whenever isWarningRef's value changes (i.e. whenever the
  // parent's isWarning prop flips true/false) — this is what actually
  // starts/stops the alarm as alerts come and go, independent of the
  // toggle button itself.
  watch(isWarningRef, (active) => {
    if (active && soundEnabled.value) {
      startAlarm()
    } else {
      stopAlarm()
    }
  })

  // Cleanup if this component is ever removed from the page — stop any
  // beeping and release the AudioContext rather than leaking it.
  onBeforeUnmount(() => {
    stopAlarm()
    if (audioCtx) {
      audioCtx.close()
      audioCtx = null
    }
  })

  // Whatever calls useVoiceAlarm() (WarningBanner.vue) destructures these out.
  return { soundEnabled, soundBlockedMessage, toggleSound }
}
