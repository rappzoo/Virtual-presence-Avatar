// Rename English Quick Sounds (Slots 21-40)
// Paste this into browser console on the Avatar Tank page

const enSoundNames = {
  20: "Hi 👋",
  21: "How are you?",
  22: "Nice to see you",
  23: "What's up?",
  24: "Take care",
  25: "Yes/No/Maybe",
  26: "I don't know",
  27: "That's funny!",
  28: "Really?",
  29: "Got it",
  30: "I like that",
  31: "Cool/Awesome",
  32: "Happy for you",
  33: "Just chilling",
  34: "Talk later",
  35: "Thank you",
  36: "You're welcome",
  37: "Sorry",
  38: "Good job",
  39: "I missed you"
};

// Get existing sound names from localStorage or create new object
let soundNames = {};
try {
  const saved = localStorage.getItem('avatarSoundNames');
  if (saved) {
    soundNames = JSON.parse(saved);
  }
} catch (e) {
  console.log('Starting fresh sound names');
}

// Add EN sound names
Object.assign(soundNames, enSoundNames);

// Save to localStorage
localStorage.setItem('avatarSoundNames', JSON.stringify(soundNames));

console.log('✅ EN sound names saved!');
console.log('Refresh the page to see the new labels.');
console.log('Total sounds named:', Object.keys(soundNames).length);

