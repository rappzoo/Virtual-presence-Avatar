// Apply English labels to sounds 21-40
// Run this in browser console on the web UI

console.log("🎵 Applying English labels to sounds 21-40...");

// English sound labels
const enLabels = {
    20: "Hi 👋",           // sound21
    21: "How are you?",     // sound22
    22: "Nice to see you",  // sound23
    23: "What's up?",       // sound24
    24: "Take care",        // sound25
    25: "Yes/No/Maybe",     // sound26
    26: "I don't know",     // sound27
    27: "That's funny!",    // sound28
    28: "Really?",          // sound29
    29: "Got it",           // sound30
    30: "I like that",      // sound31
    31: "Cool/Awesome",     // sound32
    32: "Happy for you",    // sound33
    33: "Just chilling",    // sound34
    34: "Talk later",       // sound35
    35: "Thank you",        // sound36
    36: "You're welcome",   // sound37
    37: "Sorry",            // sound38
    38: "Good job",         // sound39
    39: "I missed you"      // sound40
};

// Apply labels to localStorage
let renamedCount = 0;
for (const [soundId, label] of Object.entries(enLabels)) {
    localStorage.setItem(`sound_name_${soundId}`, label);
    renamedCount++;
    console.log(`✅ Renamed sound ${parseInt(soundId) + 1} to "${label}"`);
}

console.log(`🎉 Successfully renamed ${renamedCount} English sounds!`);
console.log("🔄 Refresh the page to see the new labels on the buttons.");

// Also update the side panel buttons if they exist
setTimeout(() => {
    console.log("🔄 Updating side panel button labels...");
    
    // Update left panel buttons (21-30)
    for (let i = 20; i < 30; i++) {
        const button = document.querySelector(`button[data-sound-id="${i}"]`);
        if (button && enLabels[i]) {
            button.textContent = enLabels[i];
            button.title = enLabels[i];
        }
    }
    
    // Update right panel buttons (31-40)
    for (let i = 30; i < 40; i++) {
        const button = document.querySelector(`button[data-sound-id="${i}"]`);
        if (button && enLabels[i]) {
            button.textContent = enLabels[i];
            button.title = enLabels[i];
        }
    }
    
    console.log("✅ Side panel labels updated!");
}, 1000);
