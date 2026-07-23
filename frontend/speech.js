// speech.js — TTS + ASR using the browser's built-in Web Speech API

// ---------- TTS: Text-to-Speech ----------
function speak(text) {
  if (!("speechSynthesis" in window)) {
    console.warn("TTS not supported in this browser");
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}

function stopSpeaking() {
  window.speechSynthesis.cancel();
}

// ---------- ASR: Speech-to-Text ----------
function startListening(onResult, onError) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("ASR not supported in this browser");
    if (onError) onError("Speech recognition not supported");
    return null;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    onResult(transcript);
  };

  recognition.onerror = (event) => {
    if (onError) onError(event.error);
  };

  recognition.start();
  return recognition;
}