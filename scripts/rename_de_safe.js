// German Sound Rename Script - Safe Version
// Paste this into browser console (won't conflict with existing variables)

(function() {
  const deLabels = {
    60: "Hallo 👋",              // sound61
    61: "Wie geht es dir?",      // sound62
    62: "Schön dich zu sehen",   // sound63
    63: "Was ist los?",          // sound64
    64: "Pass auf dich auf",     // sound65
    65: "Ja/Nein/Vielleicht",   // sound66
    66: "Ich weiß nicht",        // sound67
    67: "Das ist lustig!",       // sound68
    68: "Wirklich?",             // sound69
    69: "Verstanden",            // sound70
    70: "Das gefällt mir",       // sound71
    71: "Cool/Geil",             // sound72
    72: "Ich freue mich für dich", // sound73
    73: "Ich entspanne mich",    // sound74
    74: "Lass uns später reden", // sound75
    75: "Danke",                 // sound76
    76: "Gern geschehen",        // sound77
    77: "Entschuldigung",        // sound78
    78: "Gut gemacht",           // sound79
    79: "Ich habe dich vermisst" // sound80
  };

  // Get existing names
  let currentNames = {};
  try {
    const saved = localStorage.getItem('avatarSoundNames');
    if (saved) currentNames = JSON.parse(saved);
  } catch (e) {
    console.log('Starting fresh...');
  }

  // Add German labels
  Object.assign(currentNames, deLabels);

  // Save back
  localStorage.setItem('avatarSoundNames', JSON.stringify(currentNames));

  console.log('✅ German sound labels applied!');
  console.log('🔄 Refresh the page to see the changes.');
  console.log('📊 Total sounds named:', Object.keys(currentNames).length);
})();
