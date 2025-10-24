// Complete Multi-Language Sound Rename Script
// Renames ALL sounds: EN (21-40), RO (41-60), DE (61-80)
// Paste this into browser console

(function() {
  const allLabels = {
    // English (21-40)
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
    39: "I missed you",
    
    // Romanian (41-60)
    40: "Salut 👋",
    41: "Ce mai faci?",
    42: "Mă bucur să te văd",
    43: "Ce mai e nou?",
    44: "Ai grijă de tine",
    45: "Da/Nu/Poate",
    46: "Nu știu",
    47: "E amuzant!",
    48: "Serios?",
    49: "Am înțeles",
    50: "Îmi place",
    51: "E tare/Mișto",
    52: "Mă bucur pentru tine",
    53: "Mă relaxez",
    54: "Să vorbim mai târziu",
    55: "Mulțumesc",
    56: "Cu plăcere",
    57: "Îmi pare rău",
    58: "Bravo",
    59: "Mi-a fost dor de tine",
    
    // German (61-80)
    60: "Hallo 👋",
    61: "Wie geht es dir?",
    62: "Schön dich zu sehen",
    63: "Was ist los?",
    64: "Pass auf dich auf",
    65: "Ja/Nein/Vielleicht",
    66: "Ich weiß nicht",
    67: "Das ist lustig!",
    68: "Wirklich?",
    69: "Verstanden",
    70: "Das gefällt mir",
    71: "Cool/Geil",
    72: "Ich freue mich für dich",
    73: "Ich entspanne mich",
    74: "Lass uns später reden",
    75: "Danke",
    76: "Gern geschehen",
    77: "Entschuldigung",
    78: "Gut gemacht",
    79: "Ich habe dich vermisst"
  };

  // Get existing names
  let currentNames = {};
  try {
    const saved = localStorage.getItem('avatarSoundNames');
    if (saved) currentNames = JSON.parse(saved);
  } catch (e) {
    console.log('Starting fresh...');
  }

  // Add all labels
  Object.assign(currentNames, allLabels);

  // Save back
  localStorage.setItem('avatarSoundNames', JSON.stringify(currentNames));

  console.log('✅ ALL language sound labels applied!');
  console.log('🇬🇧 English (21-40): 20 sounds');
  console.log('🇷🇴 Romanian (41-60): 20 sounds');
  console.log('🇩🇪 German (61-80): 20 sounds');
  console.log('🔄 Refresh the page to see all changes.');
  console.log('📊 Total sounds named:', Object.keys(currentNames).length);
})();
