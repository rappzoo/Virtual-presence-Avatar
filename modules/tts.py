#!/usr/bin/env python3
"""
Text-to-Speech module for Avatar Tank system.
Handles speech synthesis using Edge-TTS (Romanian), Piper, or fallback engines.
"""

import subprocess
import shutil
import os
import glob
import asyncio
import edge_tts
import tempfile
import time
from pathlib import Path
from modules.device_detector import SPK_PLUG


class PiperTTS:
    def __init__(self):
        self.languages = {
            'en': {'name': 'English', 'dir': '/home/havatar/Avatar-robot/piper/models/en'},
            'ro': {'name': 'Română',  'dir': '/home/havatar/Avatar-robot/piper/models/ro'},
            'de': {'name': 'Deutsch', 'dir': '/home/havatar/Avatar-robot/piper/models/de'},
        }
        self.current_language='en'
        self.bin, self.kind = self._find_piper_bin()
        
        # Edge-TTS configuration for Romanian
        self.edge_voices = {
            'ro': 'ro-RO-EmilNeural'  # Romanian male voice
        }
        self.temp_dir = Path('/tmp/edge_tts_ro')
        self.temp_dir.mkdir(exist_ok=True)

    def _find_piper_bin(self):
        # prefer piper-cli, then piper
        cand = [
            os.path.expanduser("~/piper/bin/piper-cli"),
            "/home/havatar/Avatar-robot/piper/bin/piper-cli",
            "/usr/local/bin/piper-cli", "/usr/bin/piper-cli",
            os.path.expanduser("~/piper/bin/piper"),
            "/home/havatar/Avatar-robot/piper/bin/piper",
            "/usr/local/bin/piper", "/usr/bin/piper",
        ]
        for c in cand:
            if os.path.exists(c):
                return (c, "cli" if c.endswith("piper-cli") else "piper")
        # also try PATH
        for name in ["piper-cli","piper"]:
            w = shutil.which(name)
            if w: return (w, "cli" if name=="piper-cli" else "piper")
        return (None, None)

    def _find_model_pair(self, lang_dir):
        onnx = sorted(glob.glob(os.path.join(lang_dir, "*.onnx")))
        js   = sorted(glob.glob(os.path.join(lang_dir, "*.json")))
        return (onnx[0], js[0]) if onnx and js else (None, None)

    def _find_model_single(self, lang_dir):
        onnx = sorted(glob.glob(os.path.join(lang_dir, "*.onnx")))
        return onnx[0] if onnx else None

    def _fix_romanian_question_intonation(self, text):
        """Fix Romanian question intonation by preprocessing text for Piper"""
        # Remove the question mark temporarily
        text_without_q = text.rstrip('?').strip()
        
        # Different approaches for different question word patterns
        question_words = ['ce', 'cum', 'unde', 'când', 'de ce', 'cine', 'care', 'cât', 'câte', 'câți', 'câteva']
        
        # Check if text contains common Romanian question words
        text_lower = text_without_q.lower()
        has_question_word = any(word in text_lower for word in question_words)
        
        if has_question_word:
            # For questions with question words - add more emphasis and pause
            enhanced_text = f"{text_without_q}... ?"
        else:
            # For other questions - simpler approach
            enhanced_text = f"{text_without_q} ?"
        
        return enhanced_text

    def internet_available(self):
        """Check if internet connection is available"""
        try:
            import urllib.request
            urllib.request.urlopen('http://google.com', timeout=3)
            return True
        except:
            return False

    async def synthesize_edge_tts(self, text, language):
        """High-quality Edge-TTS synthesis for Romanian"""
        if language not in self.edge_voices:
            return None
        
        voice = self.edge_voices[language]
        temp_file = self.temp_dir / f"edge_tts_{int(time.time())}.mp3"
        
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(temp_file))
            return str(temp_file)
        except Exception as e:
            print(f"[TTS] Edge-TTS error: {e}")
            return None

    def play_edge_tts_audio(self, audio_file):
        """Play Edge-TTS audio using mpg123"""
        try:
            result = subprocess.run(['mpg123', '-q', str(audio_file)], 
                                  capture_output=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            print(f"[TTS] Audio playback error: {e}")
            return False

    def status(self):
        return {
            "ok": bool(self.bin),
            "binary": self.bin,
            "kind": self.kind,
            "lang": self.current_language
        }

    def speak(self, text, language=None):
        text = (text or "").strip()
        if not text:
            return {"ok": False, "msg": "empty text"}
        if language: self.current_language = language
        if self.current_language not in self.languages:
            return {"ok": False, "msg": f"unsupported lang '{self.current_language}'"}
        
        # Try Edge-TTS for Romanian if internet is available
        if self.current_language == 'ro' and self.internet_available():
            try:
                print(f"[TTS] Using Edge-TTS for Romanian: {text}")
                audio_file = asyncio.run(self.synthesize_edge_tts(text, 'ro'))
                
                if audio_file and os.path.exists(audio_file):
                    success = self.play_edge_tts_audio(audio_file)
                    # Clean up temp file
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                    
                    if success:
                        return {"ok": True, "msg": f"Spoken with Edge-TTS ({self.languages[self.current_language]['name']})"}
                    else:
                        print("[TTS] Edge-TTS playback failed, falling back to Piper")
                else:
                    print("[TTS] Edge-TTS synthesis failed, falling back to Piper")
            except Exception as e:
                print(f"[TTS] Edge-TTS error: {e}, falling back to Piper")
        
        # Fix Romanian question intonation for Piper fallback
        is_romanian_question = self.current_language == 'ro' and text.endswith('?')
        if is_romanian_question:
            text = self._fix_romanian_question_intonation(text)

        lang_dir = self.languages[self.current_language]['dir']
        # 1) Piper CLI?
        if self.bin and self.kind=="cli":
            model, cfg = self._find_model_pair(lang_dir)
            if not model or not cfg:
                return {"ok": False, "msg": f"no Piper model/cfg in {lang_dir}"}
            outwav = "/tmp/tts.wav"
            try:
                # Add length scale for Romanian questions to improve intonation
                cmd = [self.bin, "--model", model, "--config", cfg, "--output_file", outwav]
                if is_romanian_question:
                    cmd.extend(["--length_scale", "0.8"])  # Slower speech for questions
                
                p = subprocess.run(
                    cmd,
                    input=(text+"\n"), text=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False
                )
                if p.returncode!=0 or not os.path.exists(outwav) or os.path.getsize(outwav)<1000:
                    return {"ok": False, "msg": (p.stderr.decode() if hasattr(p.stderr,'decode') else p.stderr) or "piper-cli failed"}
                # play
                q = subprocess.run(["aplay","-q","-D", SPK_PLUG, outwav], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                os.unlink(outwav)
                if q.returncode!=0:
                    return {"ok": False, "msg": f"aplay error: {q.stderr.strip()}"}
                return {"ok": True, "msg": f"Spoken ({self.languages[self.current_language]['name']})"}
            except Exception as e:
                return {"ok": False, "msg": f"tts error: {e}"}

        # 2) Piper (no config file needed)
        if self.bin and self.kind=="piper":
            model = self._find_model_single(lang_dir)
            if not model:
                return {"ok": False, "msg": f"no Piper model in {lang_dir}"}
            outwav = "/tmp/tts.wav"
            try:
                # Add length scale for Romanian questions to improve intonation
                cmd = [self.bin, "--model", model, "--output_file", outwav]
                if is_romanian_question:
                    cmd.extend(["--length_scale", "0.8"])  # Slower speech for questions
                
                p = subprocess.run(
                    cmd,
                    input=(text+"\n"), text=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False
                )
                if p.returncode!=0 or not os.path.exists(outwav) or os.path.getsize(outwav)<1000:
                    return {"ok": False, "msg": (p.stderr.decode() if hasattr(p.stderr,'decode') else p.stderr) or "piper failed"}
                q = subprocess.run(["aplay","-q","-D", SPK_PLUG, outwav], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                os.unlink(outwav)
                if q.returncode!=0:
                    return {"ok": False, "msg": f"aplay error: {q.stderr.strip()}"}
                return {"ok": True, "msg": f"Spoken ({self.languages[self.current_language]['name']})"}
            except Exception as e:
                return {"ok": False, "msg": f"tts error: {e}"}

        # 3) Fallback: espeak-ng -> aplay
        try:
            es = subprocess.Popen(["espeak-ng","-v","en-us","-s","170","--stdout", text], stdout=subprocess.PIPE)
            ap = subprocess.Popen(["aplay","-q","-D", SPK_PLUG], stdin=es.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=False)
            es.stdout.close()
            ap.wait(timeout=20); es.wait(timeout=20)
            if ap.returncode!=0:
                return {"ok": False, "msg": f"espeak/aplay error: {ap.stderr.read().decode('utf-8','ignore') if ap.stderr else 'fail'}"}
            return {"ok": True, "msg": "Spoken (espeak-ng fallback)"}
        except Exception as e:
            return {"ok": False, "msg": f"no TTS engines available: {e}"}

tts = PiperTTS()