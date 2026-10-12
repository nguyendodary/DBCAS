import { useEffect, useRef, useState } from "react";

const LEARNER_PREFS_KEY = "dbcas.learner.preferences.v1";
const ACTIVE_LEARNER_KEY = "dbcas.learner.active-account.v1";
export function readLearnerPreferences() {
  try {
    const saved = JSON.parse(localStorage.getItem(LEARNER_PREFS_KEY) || "null");
    const legacy = JSON.parse(localStorage.getItem(`dbcas-learner-options:${localStorage.getItem(ACTIVE_LEARNER_KEY) || "20216000100"}`) || "null");
    const value = saved ?? legacy ?? {};
    return { fontSize: [14,16,18].includes(Number(value.fontSize)) ? Number(value.fontSize) : 16, sound: value.sound !== false, notifications: value.notifications === true, language:"vi" };
  } catch { return { fontSize:16, sound:true, notifications:false, language:"vi" }; }
}
export function saveLearnerPreferences(value) {
  const next = { ...readLearnerPreferences(), ...value };
  next.fontSize = [14,16,18].includes(Number(next.fontSize)) ? Number(next.fontSize) : 16;
  localStorage.setItem(LEARNER_PREFS_KEY, JSON.stringify(next));
  window.dispatchEvent(new CustomEvent("dbcas:learner-preferences-changed", { detail:next }));
}
export function useLearnerPreferences() {
  const [value,setValue] = useState(readLearnerPreferences);
  useEffect(() => { const sync = () => setValue(readLearnerPreferences()); window.addEventListener("storage",sync); window.addEventListener("dbcas:learner-preferences-changed",sync); return () => { window.removeEventListener("storage",sync); window.removeEventListener("dbcas:learner-preferences-changed",sync); }; },[]);
  return value;
}
let examAudio;
const activeAlarmTones = new Set();
function getExamAudio() {
  const Audio = window.AudioContext || window.webkitAudioContext;
  if (!Audio) return null;
  if (!examAudio || examAudio.state === "closed") examAudio = new Audio();
  return examAudio;
}
export function useFiveMinuteAlarm({ remaining, deadline, submitted, testId }) {
  const {sound} = useLearnerPreferences();
  const [unlocked,setUnlocked] = useState(false);
  const alarmKey = `dbcas:five-minute-alarm:${testId}:${deadline}`;
  useEffect(() => {
    if (sound) return;
    for (const tone of activeAlarmTones) {
      try { tone.stop(); tone.disconnect(); } catch { /* Tone already ended. */ }
    }
    activeAlarmTones.clear();
  }, [sound]);
  useEffect(() => {
    async function unlock() { try { const audio = getExamAudio(); if (!audio) return; await audio.resume(); setUnlocked(audio.state === "running"); } catch { /* Browser blocks audio until interaction. */ } }
    window.addEventListener("pointerdown",unlock); window.addEventListener("keydown",unlock);
    return () => { window.removeEventListener("pointerdown",unlock); window.removeEventListener("keydown",unlock); };
  },[]);
  const fired = useRef("");
  useEffect(() => {
    if (!sound || submitted || remaining <= 0 || remaining > 300 || !unlocked || fired.current === alarmKey) return;
    try { if (localStorage.getItem(alarmKey)) return; } catch { /* Still play once in this mounted attempt. */ }
    const audio = getExamAudio(); if (!audio || audio.state !== "running") return;
    fired.current = alarmKey;
    try { localStorage.setItem(alarmKey,"played"); } catch { /* In-memory deduplication is available. */ }
    for (let i=0;i<3;i++) {
      const oscillator = audio.createOscillator(), gain = audio.createGain();
      const start = audio.currentTime + i * .45;
      oscillator.type="sine"; oscillator.frequency.value = 880;
      gain.gain.setValueAtTime(0,start); gain.gain.linearRampToValueAtTime(.16,start+.02); gain.gain.exponentialRampToValueAtTime(.001,start+.3);
      oscillator.connect(gain); gain.connect(audio.destination); activeAlarmTones.add(oscillator); oscillator.start(start); oscillator.stop(start+.32);
      oscillator.onended = () => { activeAlarmTones.delete(oscillator); oscillator.disconnect(); gain.disconnect(); };
    }
  },[sound,submitted,remaining,unlocked,alarmKey]);
}

