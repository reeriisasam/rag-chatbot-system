# 🎤 Audio Setup Guide

คู่มือการติดตั้ง Audio Packages สำหรับฟีเจอร์เสียง

## 📋 Packages ที่ต้องการ

1. **PyAudio** - สำหรับเข้าถึงไมโครโฟน
2. **SpeechRecognition** - สำหรับแปลงเสียงเป็นข้อความ
3. **pyttsx3** - สำหรับแปลงข้อความเป็นเสียง
4. **openai-whisper** (optional) - สำหรับการแปลงเสียงที่แม่นยำกว่า

## 🪟 Windows

### วิธีที่ 1: ใช้ pipwin (แนะนำ)

```bash
# ติดตั้ง pipwin
pip install pipwin

# ติดตั้ง PyAudio ผ่าน pipwin
pipwin install pyaudio

# ติดตั้ง packages อื่นๆ
pip install SpeechRecognition pyttsx3
```

### วิธีที่ 2: ดาวน์โหลด Wheel File

1. ไปที่ https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. ดาวน์โหลดไฟล์ที่ตรงกับ Python version (เช่น `PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl` สำหรับ Python 3.11, 64-bit)
3. ติดตั้ง:

```bash
pip install path/to/PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl
pip install SpeechRecognition pyttsx3
```

### วิธีที่ 3: Build จาก Source (ยาก)

ต้องติดตั้ง Visual Studio Build Tools:

```bash
# ดาวน์โหลดจาก:
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# จากนั้นติดตั้ง
pip install pyaudio
pip install SpeechRecognition pyttsx3
```

## 🐧 Linux (Ubuntu/Debian)

```bash
# ติดตั้ง dependencies
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio

# ติดตั้ง Python packages
pip install pyaudio SpeechRecognition pyttsx3

# ติดตั้ง espeak สำหรับ TTS (optional)
sudo apt-get install espeak espeak-data
```

## 🍎 macOS

```bash
# ติดตั้ง portaudio ผ่าน Homebrew
brew install portaudio

# ติดตั้ง Python packages
pip install pyaudio SpeechRecognition pyttsx3
```

## ✅ การทดสอบการติดตั้ง

### 1. ทดสอบ PyAudio

```python
import pyaudio

p = pyaudio.PyAudio()
print("PyAudio version:", pyaudio.__version__)
print("Available devices:", p.get_device_count())
p.terminate()
```

### 2. ทดสอบ SpeechRecognition

```python
import speech_recognition as sr

r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something!")
    audio = r.listen(source, timeout=5)
    try:
        text = r.recognize_google(audio)
        print("You said:", text)
    except:
        print("Could not understand")
```

### 3. ทดสอบ pyttsx3

```python
import pyttsx3

engine = pyttsx3.init()
engine.say("Hello World")
engine.runAndWait()
```

### 4. ทดสอบใน RAG Chatbot

รันโปรแกรมและพิมพ์:
```
/test
```

หรือคลิกปุ่ม 🎤 Voice

## 🔧 การแก้ปัญหา

### Error: "Could not find PyAudio"

**Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

**Linux:**
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

### Error: "No module named '_portaudio'"

ลบและติดตั้งใหม่:
```bash
pip uninstall pyaudio
pip install --upgrade pyaudio
```

### Error: "Cannot find microphone"

ตรวจสอบไมโครโฟน:

**Windows:**
- ตั้งค่า → ความเป็นส่วนตัว → ไมโครโฟน
- ให้สิทธิ์แอปพลิเคชัน Python ใช้ไมโครโฟน

**Linux:**
```bash
arecord -l  # แสดงรายการอุปกรณ์
```

**macOS:**
- System Preferences → Security & Privacy → Microphone
- อนุญาต Terminal/Python

### Error: "OSError: [Errno -9996]"

ปัญหา audio device:
```python
import pyaudio
p = pyaudio.PyAudio()

# แสดงอุปกรณ์ทั้งหมด
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"{i}: {info['name']}")
```

### Error: pyttsx3 ไม่พูด (Windows)

ติดตั้ง SAPI5:
```bash
pip install comtypes
pip install pywin32
```

## 📦 Package Optional

### Whisper (การแปลงเสียงแม่นยำกว่า)

```bash
pip install openai-whisper
```

หรือใช้ faster-whisper:
```bash
pip install faster-whisper
```

### Google Speech Recognition (ฟรี)

ใช้งานได้เลยผ่าน SpeechRecognition (ไม่ต้องติดตั้งเพิ่ม)

## 🎯 การเลือก Engine

### Speech-to-Text Engines

| Engine | ความแม่นยำ | ความเร็ว | ออนไลน์ | ฟรี |
|--------|-----------|---------|---------|-----|
| Google | ดีมาก | เร็ว | ✓ | ✓ |
| Whisper | ดีที่สุด | ช้า | ✗ | ✓ |
| Sphinx | ปานกลาง | เร็ว | ✗ | ✓ |

### Text-to-Speech Engines

| Engine | คุณภาพเสียง | ความเร็ว | ออนไลน์ | ฟรี |
|--------|-----------|---------|---------|-----|
| pyttsx3 | ดี | เร็ว | ✗ | ✓ |
| gTTS | ดีมาก | ช้า | ✓ | ✓ |
| Azure TTS | ดีที่สุด | เร็ว | ✓ | ✗ |

## 💡 Tips

### 1. ใช้ Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install pyaudio SpeechRecognition pyttsx3
```

### 2. ทดสอบไมโครโฟนก่อน

```bash
# Windows: ใช้ Sound Recorder
# Linux: arecord -d 5 test.wav
# macOS: ใช้ QuickTime
```

### 3. ปรับระดับเสียง

ใน config.yaml:
```yaml
audio:
  stt:
    engine: "google"  # หรือ "whisper"
  tts:
    rate: 150  # ความเร็วในการพูด
    volume: 0.9  # ระดับเสียง
```

## 📚 ทรัพยากรเพิ่มเติม

- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/)
- [SpeechRecognition Documentation](https://github.com/Uberi/speech_recognition)
- [pyttsx3 Documentation](https://pyttsx3.readthedocs.io/)
- [Whisper Documentation](https://github.com/openai/whisper)

## 🆘 ยังติดปัญหา?

1. ตรวจสอบ Python version (แนะนำ 3.8-3.11)
2. ตรวจสอบว่ามี admin rights
3. ลองติดตั้งใน virtual environment ใหม่
4. ดู logs ที่ `logs/app.log`
5. เปิด issue ใน GitHub

---

**หมายเหตุ:** โปรแกรมสามารถทำงานได้แบบ text-only โดยไม่ต้องติดตั้ง audio packages