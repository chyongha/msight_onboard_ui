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
const BEEP_DURATION_S = 0.15
const BEEP_INTERVAL_MS = 500
const BEEP_GAIN = 0.15 // quiet-ish; this is a UI demo, not a real siren

export function useVoiceAlarm(isWarningRef) {
  const soundEnabled = ref(false)
  const soundBlockedMessage = ref('')

  let audioCtx = null
  let beepTimer = null

  function ensureContext() {
    if (!audioCtx) {
      const Ctor = window.AudioContext || window.webkitAudioContext
      audioCtx = new Ctor()
    }
    return audioCtx
  }

  function playBeep() {
    const ctx = ensureContext()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'square'
    osc.frequency.value = BEEP_FREQUENCY_HZ
    gain.gain.setValueAtTime(BEEP_GAIN, ctx.currentTime)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + BEEP_DURATION_S)
  }

  function startAlarm() {
    if (beepTimer !== null) return
    playBeep()
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
      stopAlarm()
      return
    }

    // The user-gesture requirement is satisfied right here (this only
    // runs from a click handler), so resume() should succeed. If it
    // doesn't, surface why instead of silently doing nothing.
    ensureContext().resume()
      .then(() => {
        soundBlockedMessage.value = ''
        if (isWarningRef.value) startAlarm()
      })
      .catch(() => {
        soundBlockedMessage.value = 'Voice alarm blocked until user interaction'
      })
  }

  watch(isWarningRef, (active) => {
    if (active && soundEnabled.value) {
      startAlarm()
    } else {
      stopAlarm()
    }
  })

  onBeforeUnmount(() => {
    stopAlarm()
    if (audioCtx) {
      audioCtx.close()
      audioCtx = null
    }
  })

  return { soundEnabled, soundBlockedMessage, toggleSound }
}
