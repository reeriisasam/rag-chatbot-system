#!/usr/bin/env python3
"""
ทดสอบระบบเสียง (Speech-to-Text และ Text-to-Speech)
"""

from rich.console import Console
from rich.panel import Panel

console = Console()

def test_tts():
    """ทดสอบ Text-to-Speech"""
    console.print("\n[bold cyan]🔊 ทดสอบ Text-to-Speech[/bold cyan]\n")
    
    try:
        import pyttsx3
        
        console.print("✓ pyttsx3 installed")
        
        # สร้าง engine
        engine = pyttsx3.init()
        console.print("✓ TTS engine initialized")
        
        # ดึงข้อมูล voices
        voices = engine.getProperty('voices')
        console.print(f"✓ Found {len(voices)} voices:\n")
        
        for i, voice in enumerate(voices[:5]):  # แสดงแค่ 5 ตัวแรก
            console.print(f"  {i+1}. {voice.name}")
            console.print(f"     ID: {voice.id}")
            console.print(f"     Languages: {voice.languages}\n")
        
        # ทดสอบพูด
        if console.input("\n[yellow]ต้องการทดสอบการพูดหรือไม่? (y/n): [/yellow]").lower() == 'y':
            test_text = "สวัสดีครับ นี่คือการทดสอบเสียงพูด"
            
            console.print(f"\n🔊 กำลังพูด: '{test_text}'")
            engine.say(test_text)
            engine.runAndWait()
            console.print("✓ พูดเสร็จแล้ว")
        
        console.print("\n[bold green]✅ Text-to-Speech ทำงานปกติ[/bold green]")
        return True
        
    except ImportError:
        console.print("[bold red]❌ pyttsx3 ไม่ได้ติดตั้ง[/bold red]")
        console.print("ติดตั้งด้วย: pip install pyttsx3")
        return False
    except Exception as e:
        console.print(f"[bold red]❌ เกิดข้อผิดพลาด: {e}[/bold red]")
        return False


def test_stt():
    """ทดสอบ Speech-to-Text"""
    console.print("\n[bold cyan]🎤 ทดสอบ Speech-to-Text[/bold cyan]\n")
    
    try:
        import speech_recognition as sr
        console.print("✓ SpeechRecognition installed")
        
        try:
            import pyaudio
            console.print("✓ PyAudio installed")
        except ImportError:
            console.print("[bold red]❌ PyAudio ไม่ได้ติดตั้ง[/bold red]")
            console.print("ติดตั้งด้วย:")
            console.print("  Windows: pip install pipwin && pipwin install pyaudio")
            console.print("  Linux:   sudo apt-get install portaudio19-dev && pip install pyaudio")
            console.print("  macOS:   brew install portaudio && pip install pyaudio")
            return False
        
        # สร้าง recognizer
        r = sr.Recognizer()
        
        # ทดสอบไมโครโฟน
        try:
            with sr.Microphone() as source:
                console.print("✓ Microphone detected")
                
                if console.input("\n[yellow]ต้องการทดสอบการฟังเสียงหรือไม่? (y/n): [/yellow]").lower() == 'y':
                    console.print("\n🎤 กำลังปรับระดับเสียง...")
                    r.adjust_for_ambient_noise(source, duration=1)
                    
                    console.print("🎤 พูดอะไรสักอย่าง (5 วินาที)...")
                    audio = r.listen(source, timeout=5, phrase_time_limit=5)
                    
                    console.print("🎤 กำลังแปลงเสียง...")
                    
                    try:
                        text = r.recognize_google(audio, language='th-TH')
                        console.print(f"\n✓ คุณพูดว่า: [bold green]'{text}'[/bold green]")
                    except sr.UnknownValueError:
                        console.print("[yellow]⚠️  ไม่เข้าใจเสียงที่พูด[/yellow]")
                    except sr.RequestError as e:
                        console.print(f"[red]❌ Google API error: {e}[/red]")
            
            console.print("\n[bold green]✅ Speech-to-Text ทำงานปกติ[/bold green]")
            return True
            
        except OSError as e:
            console.print(f"[bold red]❌ ไม่พบไมโครโฟน: {e}[/bold red]")
            console.print("\nตรวจสอบ:")
            console.print("  1. เสียบไมโครโฟน")
            console.print("  2. ตั้งค่าสิทธิ์ไมโครโฟนในระบบ")
            console.print("  3. ตรวจสอบว่าไมโครโฟนทำงาน")
            return False
            
    except ImportError:
        console.print("[bold red]❌ SpeechRecognition ไม่ได้ติดตั้ง[/bold red]")
        console.print("ติดตั้งด้วย: pip install SpeechRecognition")
        return False
    except Exception as e:
        console.print(f"[bold red]❌ เกิดข้อผิดพลาด: {e}[/bold red]")
        return False


def main():
    console.print(Panel(
        "[bold cyan]🔊 ทดสอบระบบเสียง RAG Chatbot[/bold cyan]\n\n"
        "จะทดสอบ:\n"
        "  1. Text-to-Speech (การพูด)\n"
        "  2. Speech-to-Text (การฟัง)",
        title="Audio Test",
        border_style="cyan"
    ))
    
    # ทดสอบ TTS
    tts_ok = test_tts()
    
    # ทดสอบ STT
    stt_ok = test_stt()
    
    # สรุป
    console.print("\n" + "="*60)
    console.print("[bold]สรุปผลการทดสอบ:[/bold]\n")
    
    if tts_ok:
        console.print("  ✅ Text-to-Speech: [green]พร้อมใช้งาน[/green]")
    else:
        console.print("  ❌ Text-to-Speech: [red]ไม่พร้อมใช้งาน[/red]")
    
    if stt_ok:
        console.print("  ✅ Speech-to-Text: [green]พร้อมใช้งาน[/green]")
    else:
        console.print("  ❌ Speech-to-Text: [red]ไม่พร้อมใช้งาน[/red]")
    
    console.print()
    
    if tts_ok and stt_ok:
        console.print("[bold green]🎉 ระบบเสียงพร้อมใช้งานครบถ้วน![/bold green]")
        console.print("\nสามารถใช้โหมดเสียงใน RAG Chatbot ได้แล้ว")
    elif tts_ok:
        console.print("[bold yellow]⚠️  สามารถพูดได้ แต่ฟังไม่ได้[/bold yellow]")
        console.print("\nติดตั้ง PyAudio เพื่อเปิดใช้การฟังเสียง")
    else:
        console.print("[bold red]❌ ระบบเสียงไม่พร้อมใช้งาน[/bold red]")
        console.print("\nกรุณาติดตั้ง audio packages ตามคำแนะนำด้านบน")
    
    console.print("\n📚 ดูคู่มือเพิ่มเติมใน: AUDIO_SETUP.md\n")


if __name__ == "__main__":
    main()