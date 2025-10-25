#!/usr/bin/env python3
"""
Quick Edge-TTS Integration for Romanian TTS
Adds high-quality Romanian TTS to existing Avatar Tank system
"""

import asyncio
import edge_tts
import os
import tempfile
from pathlib import Path

class EdgeTTSRomanian:
    """High-quality Romanian TTS using Edge-TTS"""
    
    def __init__(self):
        self.voices = {
            'female': 'ro-RO-AlinaNeural',
            'male': 'ro-RO-EmilNeural'
        }
        self.default_voice = 'female'
    
    async def synthesize_async(self, text, voice='female', output_file=None):
        """Asynchronous Edge-TTS synthesis"""
        voice_name = self.voices[voice]
        
        if output_file is None:
            output_file = tempfile.mktemp(suffix='.mp3')
        
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.async_save(output_file)
        
        return output_file
    
    def synthesize(self, text, voice='female', output_file=None):
        """Synchronous wrapper for Edge-TTS synthesis"""
        return asyncio.run(self.synthesize_async(text, voice, output_file))
    
    def test_voices(self, text="Salut, bună! Ce mai faci?"):
        """Test both Romanian voices"""
        print("🎤 Testing Edge-TTS Romanian voices...")
        
        for voice_type, voice_name in self.voices.items():
            print(f"Testing {voice_type} voice ({voice_name})...")
            try:
                output_file = self.synthesize(text, voice_type)
                print(f"✅ {voice_type} voice: {output_file}")
                print(f"   Play with: aplay {output_file}")
            except Exception as e:
                print(f"❌ {voice_type} voice failed: {e}")

def integrate_with_existing_tts():
    """Integration example for existing TTS system"""
    
    integration_code = '''
# Add this to your modules/tts.py or mediamtx_main.py

import asyncio
from edge_tts import Communicate

class ImprovedRomanianTTS:
    def __init__(self):
        self.edge_voices = {
            'female': 'ro-RO-AlinaNeural',
            'male': 'ro-RO-EmilNeural'
        }
    
    async def synthesize_edge_tts(self, text, voice='female'):
        """High-quality Romanian TTS"""
        voice_name = self.edge_voices[voice]
        communicate = Communicate(text, voice_name)
        
        # Save to temporary file
        temp_file = f"/tmp/edge_ro_{voice}_{int(time.time())}.mp3"
        await communicate.async_save(temp_file)
        
        return temp_file
    
    def synthesize_romanian(self, text, quality='high'):
        """Main Romanian TTS function with quality selection"""
        if quality == 'premium' and self.internet_available():
            # Use Edge-TTS (best quality)
            return asyncio.run(self.synthesize_edge_tts(text, 'female'))
        elif quality == 'high' and self.internet_available():
            # Use Edge-TTS male voice
            return asyncio.run(self.synthesize_edge_tts(text, 'male'))
        else:
            # Fallback to existing Piper
            return self.synthesize_piper_romanian(text)
    
    def internet_available(self):
        """Check if internet connection is available"""
        try:
            import urllib.request
            urllib.request.urlopen('http://google.com', timeout=3)
            return True
        except:
            return False

# Usage in your existing code:
# Replace your current Romanian TTS calls with:
# tts_engine = ImprovedRomanianTTS()
# audio_file = tts_engine.synthesize_romanian(text, quality='premium')
'''
    
    print("🔧 Integration Code:")
    print("=" * 50)
    print(integration_code)

def regenerate_romanian_sounds():
    """Regenerate Romanian sound effects with Edge-TTS"""
    
    romanian_expressions = {
        40: "Salut, bună",
        41: "Ce mai faci?",
        42: "Mă bucur să te văd",
        43: "Ce mai e nou?",
        44: "Ai grijă de tine",
        45: "Da, nu, poate",
        46: "Nu știu",
        47: "E amuzant!",
        48: "Serios?",
        49: "Am înțeles",
        50: "Îmi place",
        51: "E tare, e mișto",
        52: "Mă bucur pentru tine",
        53: "Mă relaxez, mă odihnesc",
        54: "Să vorbim mai târziu",
        55: "Mulțumesc",
        56: "Cu plăcere",
        57: "Îmi pare rău",
        58: "Bravo, felicitări",
        59: "Mi-a fost dor de tine"
    }
    
    print("🔄 Regenerating Romanian sounds with Edge-TTS...")
    print("=" * 50)
    
    edge_tts = EdgeTTSRomanian()
    sounds_dir = Path("/home/havatar/Avatar-robot/sounds")
    
    for sound_id, text in romanian_expressions.items():
        try:
            print(f"Generating sound{sound_id + 1}.mp3: '{text}'")
            
            # Generate with Edge-TTS
            temp_file = edge_tts.synthesize(text, 'female')
            
            # Copy to sounds directory
            output_file = sounds_dir / f"sound{sound_id + 1}.mp3"
            os.system(f"cp {temp_file} {output_file}")
            
            # Clean up temp file
            os.remove(temp_file)
            
            print(f"✅ Generated: {output_file}")
            
        except Exception as e:
            print(f"❌ Failed to generate sound{sound_id + 1}: {e}")

def main():
    """Main function"""
    print("🇷🇴 Edge-TTS Romanian Integration")
    print("=" * 50)
    
    # Test Edge-TTS
    edge_tts = EdgeTTSRomanian()
    edge_tts.test_voices()
    
    print("\n" + "=" * 50)
    
    # Show integration code
    integrate_with_existing_tts()
    
    print("\n" + "=" * 50)
    
    # Ask about regenerating sounds
    response = input("🔄 Regenerate Romanian sounds with Edge-TTS? (y/n): ")
    if response.lower() == 'y':
        regenerate_romanian_sounds()
    
    print("\n✅ Integration complete!")
    print("💡 Next steps:")
    print("   1. Test the generated audio files")
    print("   2. Integrate Edge-TTS into your TTS module")
    print("   3. Update web interface with quality selector")

if __name__ == "__main__":
    main()
