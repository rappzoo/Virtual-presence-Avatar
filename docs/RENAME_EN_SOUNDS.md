# 🏷️ How to Rename English Sounds (21-40)

## Quick Method (Recommended)

1. **Open the web interface:**
   ```
   http://192.168.68.107:5000
   ```

2. **Open browser console:**
   - Press **F12** (or right-click → Inspect)
   - Click **Console** tab

3. **Paste and run the rename script:**
   - Copy the contents of `/home/havatar/Avatar-robot/scripts/rename_en_sounds.js`
   - Paste into console
   - Press **Enter**

4. **Refresh the page:**
   - Press **F5** or **Ctrl+R**
   - The buttons should now show friendly labels!

## What Will Happen

The script will rename all 20 English sounds:

### Left Panel (21-30):
- 21: "Hi 👋"
- 22: "How are you?"
- 23: "Nice to see you"
- 24: "What's up?"
- 25: "Take care"
- 26: "Yes/No/Maybe"
- 27: "I don't know"
- 28: "That's funny!"
- 29: "Really?"
- 30: "Got it"

### Right Panel (31-40):
- 31: "I like that"
- 32: "Cool/Awesome"
- 33: "Happy for you"
- 34: "Just chilling"
- 35: "Talk later"
- 36: "Thank you"
- 37: "You're welcome"
- 38: "Sorry"
- 39: "Good job"
- 40: "I missed you"

## Alternative: Manual Rename

If you prefer to rename manually:

1. Click **Rename** button in the motor panel
2. Click any sound button (21-40)
3. Type the new name
4. Click **Done** when finished

## Verification

After running the script and refreshing:
- Side panel buttons should show friendly labels instead of numbers
- Hovering over buttons should show the full text
- Clicking buttons should play the corresponding English expressions

---

**Note:** The rename script uses localStorage, so the labels will persist across browser sessions and page refreshes.
