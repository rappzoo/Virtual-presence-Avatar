// Simple English Sound Rename - Safe Version
// Paste this into browser console (won't conflict with existing variables)

(function() {
  const enLabels = {
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

  // Get existing names
  let currentNames = {};
  try {
    const saved = localStorage.getItem('avatarSoundNames');
    if (saved) currentNames = JSON.parse(saved);
  } catch (e) {
    console.log('Starting fresh...');
  }

  // Add English labels
  Object.assign(currentNames, enLabels);

  // Save back
  localStorage.setItem('avatarSoundNames', JSON.stringify(currentNames));

  console.log('✅ English sound labels applied!');
  console.log('🔄 Refresh the page to see the changes.');
  console.log('📊 Total sounds named:', Object.keys(currentNames).length);
})();
