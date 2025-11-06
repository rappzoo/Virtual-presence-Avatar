#!/usr/bin/env python3
"""
Romanian TTS Quality Comparison Script
Tests different TTS engines for Romanian language quality
"""

import os
import subprocess
import sys
from pathlib import Path

def test_piper_romanian(text, output_file):
    """Test current Piper Romanian model"""
    try:
        piper_path = "/home/havatar/Avatar-robot/piper/bin/piper"
        model_path = "/home/havatar/Avatar-robot/piper/models/ro/ro_RO-mihai-medium.onnx"
        
        cmd = [
            piper_path,
            "--model", model_path,
            "--output_file", output_file
        ]
        
        result = subprocess.run(cmd, input=text, text=True, capture_output=True)
        if result.returncode == 0:
            print(f"✅ Piper Romanian: {output_file}")
            return True
        else:
            print(f"❌ Piper Romanian failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Piper Romanian error: {e}")
        return False

def test_edge_tts_romanian(text, output_file, voice="ro-RO-AlinaNeural"):
    """Test Edge-TTS Romanian voices"""
    try:
        cmd = [
            "edge-tts",
            "--voice", voice,
            "--text", text,
            "--write-media", output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Edge-TTS Romanian ({voice}): {output_file}")
            return True
        else:
            print(f"❌ Edge-TTS Romanian failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Edge-TTS Romanian error: {e}")
        return False

def test_google_tts_romanian(text, output_file):
    """Test Google TTS Romanian"""
    try:
        from gtts import gTTS
        tts = gTTS(text, lang='ro')
        tts.save(output_file)
        print(f"✅ Google TTS Romanian: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Google TTS Romanian error: {e}")
        return False

def test_festival_romanian(text, output_file):
    """Test Festival Romanian (if available)"""
    try:
        cmd = ["festival", "--tts"]
        result = subprocess.run(cmd, input=text, text=True, capture_output=True)
        if result.returncode == 0:
            print(f"✅ Festival Romanian: {output_file}")
            return True
        else:
            print(f"❌ Festival Romanian failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Festival Romanian error: {e}")
        return False

def main():
    """Main comparison function"""
    print("🎤 Romanian TTS Quality Comparison")
    print("=" * 50)
    
    # Test text in Romanian
    test_text = "Salut, bună! Ce mai faci? Mă bucur să te văd. Cum te simți astăzi?"
    
    print(f"Test text: {test_text}")
    print()
    
    # Create output directory
    output_dir = Path("/tmp/romanian_tts_test")
    output_dir.mkdir(exist_ok=True)
    
    results = {}
    
    # Test Piper (current)
    print("1. Testing Piper Romanian (current)...")
    results['piper'] = test_piper_romanian(test_text, str(output_dir / "piper_ro.mp3"))
    
    # Test Edge-TTS Female
    print("\n2. Testing Edge-TTS Romanian Female...")
    results['edge_female'] = test_edge_tts_romanian(test_text, str(output_dir / "edge_ro_female.mp3"), "ro-RO-AlinaNeural")
    
    # Test Edge-TTS Male
    print("\n3. Testing Edge-TTS Romanian Male...")
    results['edge_male'] = test_edge_tts_romanian(test_text, str(output_dir / "edge_ro_male.mp3"), "ro-RO-EmilNeural")
    
    # Test Google TTS
    print("\n4. Testing Google TTS Romanian...")
    results['google'] = test_google_tts_romanian(test_text, str(output_dir / "google_ro.mp3"))
    
    # Test Festival
    print("\n5. Testing Festival Romanian...")
    results['festival'] = test_festival_romanian(test_text, str(output_dir / "festival_ro.wav"))
    
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY:")
    print("=" * 50)
    
    for engine, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{engine:15} : {status}")
    
    print(f"\n📁 Test files saved to: {output_dir}")
    print("\n🎧 To test audio quality, play the files:")
    for file in output_dir.glob("*"):
        print(f"   aplay {file}")
    
    print("\n💡 RECOMMENDATIONS:")
    if results.get('edge_female') or results.get('edge_male'):
        print("   🥇 Edge-TTS: High-quality neural voices (requires internet)")
    if results.get('google'):
        print("   🥈 Google TTS: Good quality, reliable (requires internet)")
    if results.get('piper'):
        print("   🥉 Piper: Current choice, offline but lower quality")
    
    return results

if __name__ == "__main__":
    main()
