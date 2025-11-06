#!/usr/bin/env python3
"""
Edge-TTS Romanian Male Voice Integration for Avatar Tank
High-quality Romanian TTS using Microsoft's neural voice
"""

import asyncio
import edge_tts
import os
import tempfile
import subprocess
from pathlib import Path

class EdgeTTSRomanianMale:
    """High-quality Romanian TTS using Edge-TTS male voice"""
    
    def __init__(self):
        self.voice = 'ro-RO-EmilNeural'  # Romanian male voice
        self.temp_dir = Path('/tmp/edge_tts_ro')
        self.temp_dir.mkdir(exist_ok=True)
    
    async def synthesize_async(self, text, output_file=None):
        """Asynchronous Edge-TTS synthesis"""
        if output_file is None:
            output_file = self.temp_dir / f"ro_male_{int(time.time())}.mp3"
        
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(output_file))
        
        return str(output_file)
    
    def synthesize(self, text, output_file=None):
        """Synchronous wrapper for Edge-TTS synthesis"""
        return asyncio.run(self.synthesize_async(text, output_file))
    
    def play_audio(self, audio_file):
        """Play audio file using mpg123 (handles MP3 properly)"""
        try:
            result = subprocess.run(['mpg123', '-q', str(audio_file)], 
                                  capture_output=True, timeout=30)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("Audio playback timed out")
            return False
        except Exception as e:
            print(f"Audio playback error: {e}")
            return False
    
    def test_voice(self, text="Salut, bună! Ce mai faci? Mă bucur să te văd."):
        """Test the Romanian male voice"""
        print(f"🎤 Testing Romanian male voice: '{text}'")
        
        try:
            audio_file = self.synthesize(text)
            print(f"✅ Generated: {audio_file}")
            
            print("🔊 Playing audio...")
            success = self.play_audio(audio_file)
            
            if success:
                print("✅ Audio played successfully!")
            else:
                print("❌ Audio playback failed")
            
            return audio_file
            
        except Exception as e:
            print(f"❌ Voice test failed: {e}")
            return None

def integrate_with_avatar_tank():
    """Integration code for Avatar Tank system"""
    
    integration_code = '''
# Add this to your modules/mediamtx_main.py

import asyncio
import edge_tts
import subprocess
import tempfile
from pathlib import Path

class ImprovedRomanianTTS:
    def __init__(self):
        self.voice = 'ro-RO-EmilNeural'  # Romanian male voice
        self.temp_dir = Path('/tmp/edge_tts_ro')
        self.temp_dir.mkdir(exist_ok=True)
    
    async def synthesize_edge_tts(self, text):
        """High-quality Romanian TTS using Edge-TTS"""
        temp_file = self.temp_dir / f"ro_male_{int(time.time())}.mp3"
        
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(temp_file))
        
        return str(temp_file)
    
    def synthesize_romanian(self, text, quality='high'):
        """Main Romanian TTS function"""
        if quality in ['high', 'premium'] and self.internet_available():
            # Use Edge-TTS (best quality)
            return asyncio.run(self.synthesize_edge_tts(text))
        else:
            # Fallback to existing Piper
            return self.synthesize_piper_romanian(text)
    
    def play_romanian_audio(self, audio_file):
        """Play Romanian audio using mpg123"""
        try:
            result = subprocess.run(['mpg123', '-q', str(audio_file)], 
                                  capture_output=True, timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def internet_available(self):
        """Check internet connection"""
        try:
            import urllib.request
            urllib.request.urlopen('http://google.com', timeout=3)
            return True
        except:
            return False

# Usage in your existing TTS functions:
# Replace Romanian TTS calls with:
# romanian_tts = ImprovedRomanianTTS()
# audio_file = romanian_tts.synthesize_romanian(text, quality='high')
# romanian_tts.play_romanian_audio(audio_file)
'''
    
    print("🔧 Integration Code for Avatar Tank:")
    print("=" * 60)
    print(integration_code)

def regenerate_romanian_sounds():
    """Regenerate Romanian sound effects with Edge-TTS male voice"""
    
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
    
    print("🔄 Regenerating Romanian sounds with Edge-TTS male voice...")
    print("=" * 60)
    
    edge_tts = EdgeTTSRomanianMale()
    sounds_dir = Path("/home/havatar/Avatar-robot/sounds")
    
    success_count = 0
    
    for sound_id, text in romanian_expressions.items():
        try:
            print(f"Generating sound{sound_id + 1}.mp3: '{text}'")
            
            # Generate with Edge-TTS male voice
            temp_file = edge_tts.synthesize(text)
            
            if temp_file:
                # Copy to sounds directory
                output_file = sounds_dir / f"sound{sound_id + 1}.mp3"
                os.system(f"cp '{temp_file}' '{output_file}'")
                
                # Clean up temp file
                os.remove(temp_file)
                
                print(f"✅ Generated: {output_file}")
                success_count += 1
            else:
                print(f"❌ Failed to generate sound{sound_id + 1}")
            
        except Exception as e:
            print(f"❌ Error generating sound{sound_id + 1}: {e}")
    
    print(f"\n📊 Results: {success_count}/{len(romanian_expressions)} sounds generated successfully")
    
    if success_count > 0:
        print("\n🎧 Test the new sounds:")
        print("   mpg123 /home/havatar/Avatar-robot/sounds/sound41.mp3")
        print("   mpg123 /home/havatar/Avatar-robot/sounds/sound42.mp3")

def main():
    """Main function"""
    print("🇷🇴 Edge-TTS Romanian Male Voice Integration")
    print("=" * 60)
    
    # Test Edge-TTS male voice
    edge_tts = EdgeTTSRomanianMale()
    test_file = edge_tts.test_voice()
    
    if test_file:
        print(f"\n✅ Romanian male voice test successful!")
        print(f"📁 Test file: {test_file}")
        print("🎧 You can replay it with: mpg123", test_file)
    else:
        print("\n❌ Romanian male voice test failed!")
        return
    
    print("\n" + "=" * 60)
    
    # Show integration code
    integrate_with_avatar_tank()
    
    print("\n" + "=" * 60)
    
    # Ask about regenerating sounds
    print("\n🔄 Would you like to regenerate Romanian sounds with Edge-TTS male voice?")
    print("   This will replace sounds 41-60 with high-quality Romanian male voice")
    
    try:
        response = input("   Continue? (y/n): ").lower().strip()
        if response == 'y':
            regenerate_romanian_sounds()
        else:
            print("   Skipping sound regeneration")
    except KeyboardInterrupt:
        print("\n   Cancelled by user")
    
    print("\n✅ Integration complete!")
    print("\n💡 Next steps:")
    print("   1. Test the generated audio files with mpg123")
    print("   2. Integrate Edge-TTS into your TTS module")
    print("   3. Update web interface to use Edge-TTS for Romanian")
    print("   4. Add internet connectivity check")

if __name__ == "__main__":
    import time
    main()
