import { ref, watch, onBeforeUnmount } from 'vue'

const BEEP_FREQUENCY_HZ = 880 // volume level (A5)
const BEEP_DURATION_S = 0.15  // 150ms 
const BEEP_INTERVAL_MS = 500  // beep interval 500ms 
const BEEP_GAIN = 0.15 // volume, 0 (silent) to 1 (full) 

export function useVoiceAlarm(isWarningRef) {
  const soundEnabled = ref(false) // has the user clicked "Enable voice alarm"?
  const soundBlockedMessage = ref('')  // set if the browser refused to let audio play

  let audioCtx = null   // the web audio API context 
  let beepTimer = null  // the id of the repeating setInterval() driving the beeps, or null if not currently beeping

  function ensureContext() {
    if (!audioCtx) {
      const Ctor = window.AudioContext || window.webkitAudioContext  // calling audio api 
      audioCtx = new Ctor()
    }
    return audioCtx
  }

  function playBeep() {
    const ctx = ensureContext()
    const osc = ctx.createOscillator() // generates the actual tone
    const gain = ctx.createGain() // controls its volume
    osc.type = 'square'     // waveform shape 
    osc.frequency.value = BEEP_FREQUENCY_HZ
    gain.gain.setValueAtTime(BEEP_GAIN, ctx.currentTime)
    osc.connect(gain)
    gain.connect(ctx.destination)
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
      // if its turned off, stop immediately 
      stopAlarm()
      return
    }

    ensureContext().resume()  // resume() is a Promise — AudioContext can start "suspended" and needs this call to actually allow sound
      .then(() => {
        soundBlockedMessage.value = ''
        if (isWarningRef.value) startAlarm()  // if a warning is already active when sound gets enabled, start beeping right away
      })
      .catch(() => {
        soundBlockedMessage.value = 'Voice alarm blocked until user interaction'
      })
  }

  // runs whenever isWarningRef's value changes 
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
