// Romanian Sound Rename Script - Safe Version
// Paste this into browser console (won't conflict with existing variables)

(function() {
  const roLabels = {
    40: "Salut 👋",           // sound41
    41: "Ce mai faci?",       // sound42
    42: "Mă bucur să te văd", // sound43
    43: "Ce mai e nou?",      // sound44
    44: "Ai grijă de tine",   // sound45
    45: "Da/Nu/Poate",        // sound46
    46: "Nu știu",            // sound47
    47: "E amuzant!",         // sound48
    48: "Serios?",            // sound49
    49: "Am înțeles",         // sound50
    50: "Îmi place",          // sound51
    51: "E tare/Mișto",       // sound52
    52: "Mă bucur pentru tine", // sound53
    53: "Mă relaxez",         // sound54
    54: "Să vorbim mai târziu", // sound55
    55: "Mulțumesc",          // sound56
    56: "Cu plăcere",         // sound57
    57: "Îmi pare rău",       // sound58
    58: "Bravo",              // sound59
    59: "Mi-a fost dor de tine" // sound60
  };

  // Get existing names
  let currentNames = {};
  try {
    const saved = localStorage.getItem('avatarSoundNames');
    if (saved) currentNames = JSON.parse(saved);
  } catch (e) {
    console.log('Starting fresh...');
  }

  // Add Romanian labels
  Object.assign(currentNames, roLabels);

  // Save back
  localStorage.setItem('avatarSoundNames', JSON.stringify(currentNames));

  console.log('✅ Romanian sound labels applied!');
  console.log('🔄 Refresh the page to see the changes.');
  console.log('📊 Total sounds named:', Object.keys(currentNames).length);
})();
