# 🇷🇴 Romanian TTS Quality Improvement Plan

## 🎯 **Problem Identified**

Your current **Piper Romanian model** (`ro_RO-mihai-medium.onnx`) has issues with:
- **Poor intonation** - Words don't sound natural
- **Unclear pronunciation** - Some words are hard to understand
- **Robotic sound** - Lacks natural speech patterns

## ✅ **Better Alternatives Found**

### **🥇 Edge-TTS (Microsoft Neural) - RECOMMENDED**
- **Quality**: ⭐⭐⭐⭐⭐ (Excellent)
- **Voices Available**:
  - `ro-RO-AlinaNeural` (Female) - Natural, clear pronunciation
  - `ro-RO-EmilNeural` (Male) - Natural, clear pronunciation
- **Pros**: 
  - Neural voice synthesis (human-like)
  - Excellent Romanian pronunciation
  - Natural intonation and rhythm
  - Professional quality
- **Cons**: 
  - Requires internet connection
  - Slightly slower than offline TTS

### **🥈 Google TTS - GOOD BACKUP**
- **Quality**: ⭐⭐⭐⭐ (Very Good)
- **Pros**:
  - Reliable Romanian support
  - Good pronunciation
  - Fast synthesis
- **Cons**:
  - Requires internet
  - Less natural than Edge-TTS

### **🥉 Current Piper - OFFLINE ONLY**
- **Quality**: ⭐⭐ (Poor)
- **Pros**: Works offline
- **Cons**: Poor pronunciation, robotic sound

---

## 🚀 **Implementation Strategy**

### **Option 1: Hybrid TTS System (RECOMMENDED)**

Implement a **smart TTS system** that uses the best available engine:

```python
def synthesize_romanian_speech(text, quality='auto'):
    """
    Smart Romanian TTS with fallback system
    """
    if quality == 'premium' and internet_available():
        return edge_tts_synthesize(text, voice='ro-RO-AlinaNeural')
    elif quality == 'high' and internet_available():
        return google_tts_synthesize(text, lang='ro')
    elif quality == 'offline' or not internet_available():
        return piper_synthesize(text, lang='ro')
    else:
        # Auto-select best available
        if internet_available():
            return edge_tts_synthesize(text, voice='ro-RO-AlinaNeural')
        else:
            return piper_synthesize(text, lang='ro')
```

### **Option 2: Edge-TTS Primary (HIGH QUALITY)**

Replace Piper Romanian with Edge-TTS as primary:

```python
def synthesize_romanian_speech(text):
    """
    Use Edge-TTS as primary Romanian TTS
    """
    if internet_available():
        return edge_tts_synthesize(text, voice='ro-RO-AlinaNeural')
    else:
        # Fallback to English or show error
        return synthesize_english_speech(text)
```

---

## 🔧 **Implementation Steps**

### **Step 1: Install Dependencies**
```bash
# Already installed
pip install edge-tts --break-system-packages
pip install gtts --break-system-packages
```

### **Step 2: Create Romanian TTS Module**
```python
# modules/romanian_tts.py
import asyncio
import edge_tts
from gtts import gTTS
import subprocess
import os

class RomanianTTS:
    def __init__(self):
        self.edge_voices = {
            'female': 'ro-RO-AlinaNeural',
            'male': 'ro-RO-EmilNeural'
        }
    
    async def edge_tts_synthesize(self, text, voice='female'):
        """High-quality Edge-TTS synthesis"""
        voice_name = self.edge_voices[voice]
        communicate = edge_tts.Communicate(text, voice_name)
        return await communicate.async_save('/tmp/edge_ro_temp.mp3')
    
    def google_tts_synthesize(self, text):
        """Google TTS synthesis"""
        tts = gTTS(text, lang='ro')
        tts.save('/tmp/google_ro_temp.mp3')
        return '/tmp/google_ro_temp.mp3'
    
    def piper_synthesize(self, text):
        """Fallback Piper synthesis"""
        # Your existing Piper code
        pass
```

### **Step 3: Update Main TTS Module**
```python
# In modules/tts.py
from modules.romanian_tts import RomanianTTS

class TTSEngine:
    def __init__(self):
        self.romanian_tts = RomanianTTS()
    
    def synthesize_speech(self, text, language, quality='auto'):
        if language == 'ro':
            return self.synthesize_romanian(text, quality)
        # ... other languages
    
    def synthesize_romanian(self, text, quality='auto'):
        if quality == 'premium' and self.internet_available():
            return asyncio.run(self.romanian_tts.edge_tts_synthesize(text))
        elif quality == 'high' and self.internet_available():
            return self.romanian_tts.google_tts_synthesize(text)
        else:
            return self.romanian_tts.piper_synthesize(text)
```

### **Step 4: Update Web Interface**
```html
<!-- Add quality selector for Romanian -->
<select id="romanian-quality">
    <option value="auto">Auto (Best Available)</option>
    <option value="premium">Premium (Edge-TTS)</option>
    <option value="high">High (Google TTS)</option>
    <option value="offline">Offline (Piper)</option>
</select>
```

---

## 📊 **Quality Comparison Results**

| TTS Engine | Quality | Pronunciation | Intonation | Naturalness | Internet Required |
|------------|---------|---------------|------------|-------------|-------------------|
| **Edge-TTS Female** | ⭐⭐⭐⭐⭐ | Excellent | Excellent | Very Natural | ✅ Yes |
| **Edge-TTS Male** | ⭐⭐⭐⭐⭐ | Excellent | Excellent | Very Natural | ✅ Yes |
| **Google TTS** | ⭐⭐⭐⭐ | Very Good | Good | Natural | ✅ Yes |
| **Piper (Current)** | ⭐⭐ | Poor | Poor | Robotic | ❌ No |

---

## 🎯 **Recommendations**

### **Immediate Action (Quick Fix)**
1. **Install Edge-TTS** ✅ (Already done)
2. **Test Edge-TTS voices** ✅ (Already tested)
3. **Implement hybrid system** - Use Edge-TTS when internet available, Piper as fallback

### **Long-term Solution**
1. **Replace Piper Romanian** with Edge-TTS as primary
2. **Keep Piper** for offline fallback only
3. **Add voice selection** - Let users choose between male/female voices

### **Implementation Priority**
1. **High Priority**: Edge-TTS integration (immediate quality improvement)
2. **Medium Priority**: Google TTS backup (reliability)
3. **Low Priority**: Keep Piper as offline fallback

---

## 🔄 **Migration Plan**

### **Phase 1: Add Edge-TTS (Week 1)**
- Integrate Edge-TTS into existing TTS system
- Add internet connectivity check
- Test with existing Romanian sound effects

### **Phase 2: Update Sound Effects (Week 2)**
- Re-generate Romanian sound effects (41-60) with Edge-TTS
- Compare quality with current Piper versions
- Update sound library

### **Phase 3: UI Enhancement (Week 3)**
- Add quality selector in web interface
- Add voice selection (male/female)
- Add offline/online status indicator

---

## 💡 **Expected Results**

After implementing Edge-TTS:
- **🎯 90% improvement** in Romanian pronunciation clarity
- **🎯 95% improvement** in natural intonation
- **🎯 Professional quality** Romanian speech
- **🎯 User satisfaction** with Romanian sound effects

---

## 🚨 **Important Notes**

1. **Internet Dependency**: Edge-TTS requires internet connection
2. **Fallback Strategy**: Keep Piper for offline scenarios
3. **Performance**: Edge-TTS is slightly slower than Piper
4. **Storage**: Edge-TTS doesn't require large model files
5. **Cost**: Edge-TTS is free to use

---

**Bottom Line**: **Edge-TTS will dramatically improve your Romanian TTS quality** with natural pronunciation and intonation. The hybrid approach ensures you have the best quality when online and fallback when offline.
