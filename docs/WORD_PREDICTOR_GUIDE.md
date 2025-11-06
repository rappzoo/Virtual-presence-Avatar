# Word Predictor - User Guide

## Overview

The Avatar Tank word predictor is designed as an **accessibility aid for disabled users** to make typing faster and easier. It learns from your usage and gets smarter over time.

## How It Works

### 1. **As You Type**
- Start typing any word (e.g., "hel")
- Prediction pills appear showing completions: "hello", "help", "helmet", "healthy"
- Click any pill to complete the word
- The word is inserted with a space, ready for the next word

### 2. **After Completing a Word**
- Press **spacebar** to complete a word
- The word is **automatically learned** for future predictions
- New predictions appear for the **next word** based on context

### 3. **Smart Context Prediction**
- If you type "good" and press space, it might suggest: "morning", "afternoon", "evening", "night"
- If you type "thank" and press space, it might suggest: "you", "god", "goodness"
- The system learns word pairs from your usage

### 4. **Continuous Learning**
- **Every word you type** is learned automatically
- **Every pill you click** is learned
- **Every sentence you speak** is learned
- Word pairs are remembered for context predictions
- Your vocabulary grows with use

## Features

### ✅ **Multi-Word Sentences**
- Predictions work for **every word**, not just the first
- Context builds as you type
- Smarter suggestions based on previous words

### ✅ **No Text Destruction**
- Pills **insert** words, never replace previous text
- Your writing is always preserved
- Cursor moves to the right position automatically

### ✅ **Intelligent Learning**
- Learns words when you type them
- Learns words when you select pills
- Learns word pairs for better context
- Frequencies tracked for better ranking

### ✅ **Server + Client Predictions**
- Combines local word database (fast)
- With server-based dictionary (comprehensive)
- Merges and ranks by relevance

### ✅ **Multilingual Support**
- Works with English, Romanian, German
- Language-specific dictionaries
- Context learning per language

## Keyboard Shortcuts

- **Type** - Start typing to see predictions
- **Click pill** - Complete word and move to next
- **Spacebar** - Complete current word and learn it
- **Escape** - Hide prediction pills
- **Enter** - Speak the complete sentence

## Tips for Best Results

### 1. **Let It Learn**
- The more you use it, the better it gets
- Your frequently-used words appear first
- Your common phrases are remembered

### 2. **Use the Pills**
- Clicking pills is faster than typing
- Pills teach the system your vocabulary
- Context builds from pill selections

### 3. **Type Naturally**
- Don't worry about the predictions at first
- Let the system learn your writing style
- After a few sessions, predictions improve dramatically

### 4. **Check the Console**
- Open browser console (F12) to see prediction logic
- Useful for understanding what the system is doing
- Shows: word extraction, context detection, suggestion sources

## Technical Details

### Word Database
- Stored in browser localStorage
- Persists across sessions
- Per-language databases

### Context Database
- Learns word pairs: "good morning", "thank you", etc.
- Ranks by frequency
- Suggests next word based on previous word

### Learning Process
```
1. You type "hel" → Server suggests ["hello", "help", "helmet"]
2. You click "hello" → Word learned with frequency +1
3. You press space → Context updated
4. System sees you just wrote "hello"
5. Suggests common next words: "there", "world", "everyone"
6. You click "world" → Pair "hello world" learned
7. Next time you type "hel" and select "hello"
8. System suggests "world" first because of learned pair
```

### Prediction Flow
```
Typing "hel":
- Extract partial word: "hel"
- Find words starting with "hel" in database
- Rank by frequency
- Merge with server predictions
- Show top 4

After space (empty partial):
- Extract previous word
- Find word pairs starting with previous word
- Rank by frequency
- Fall back to common words
- Show top 4
```

## Troubleshooting

### Pills Replace Previous Words
✅ **Fixed** - Pills now properly insert at cursor position

### Predictions Don't Appear After First Word
✅ **Fixed** - Predictions work continuously for all words

### Words I Type Aren't Learned
✅ **Fixed** - All typed words are learned automatically

### Predictions Not Context-Aware
✅ **Fixed** - Context detection and word pairs implemented

### How to Reset Learning
If you want to start fresh:
1. Open browser console (F12)
2. Run: `localStorage.removeItem('avatarWordDatabase')`
3. Run: `localStorage.removeItem('avatarContextDatabase')`
4. Refresh the page

## Accessibility Features

### For Motor Impairments
- Large clickable pill buttons
- Keyboard shortcuts reduce typing
- Space + pills = minimal keystrokes

### For Cognitive Support
- Visual word suggestions reduce spelling burden
- Context predictions reduce decision fatigue
- Learning from usage = personalized vocabulary

### For Communication Aids
- Fast phrase building
- Learned phrases become accessible
- Natural sentence construction

## Future Improvements

Potential enhancements being considered:
- **Phrase suggestions** - Learn multi-word phrases
- **Synonym suggestions** - Offer alternative words
- **Grammar awareness** - Better part-of-speech detection
- **Voice input integration** - Dictate to learn faster
- **Export/Import** - Share learned vocabulary across devices
- **Smart autocorrect** - Fix common typos automatically

## Support

This feature is designed to help disabled users communicate more easily. If you have suggestions for improvements or encounter issues, please report them. Your feedback helps make this tool better for everyone who needs it.

## Credits

Built with care for accessibility and usability. Every improvement is tested with real-world communication needs in mind.

---

**Remember**: The predictor gets better the more you use it. Give it a few typing sessions to learn your style, and you'll see dramatically improved predictions!
