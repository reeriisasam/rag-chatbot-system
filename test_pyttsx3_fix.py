import pyttsx3
import time

print("ทดสอบ pyttsx3 แบบต่างๆ")

# วิธีที่ 1: ปกติ
print("\n1. ทดสอบแบบปกติ...")
engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)
engine.say("สวัสดีครับ นี่คือการทดสอบเสียง แบบที่หนึ่ง")
engine.runAndWait()
del engine
time.sleep(1)

# วิธีที่ 2: เปลี่ยน voice
print("\n2. ทดสอบเปลี่ยน voice...")
engine = pyttsx3.init()
voices = engine.getProperty('voices')
if len(voices) > 1:
    engine.setProperty('voice', voices[1].id)  # ลอง voice ที่ 2
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)
engine.say("สวัสดีครับ นี่คือการทดสอบเสียง แบบที่สอง")
engine.runAndWait()
del engine
time.sleep(1)

# วิธีที่ 3: ใช้ภาษาอังกฤษ
print("\n3. ทดสอบภาษาอังกฤษ...")
engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)
engine.say("Hello, this is a test in English ")
engine.runAndWait()
del engine

print("\nเสร็จแล้ว! ได้ยินเสียงไหม?")