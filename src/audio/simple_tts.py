"""
Simple TTS wrapper ที่ทำงานได้แน่นอน
ใช้วิธีเดียวกับ test_pyttsx3_fix.py ที่ได้ยินเสียง
"""

from loguru import logger

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.error("pyttsx3 not installed")


def speak_simple(text: str, rate: int = 180, volume: float = 1.0) -> bool:
    """
    พูดข้อความแบบง่ายๆ (เหมือน test script ที่ได้ยิน)
    
    Args:
        text: ข้อความที่ต้องการพูด
        rate: ความเร็ว (50-300)
        volume: ระดับเสียง (0.0-1.0)
    
    Returns:
        True ถ้าพูดสำเร็จ, False ถ้าล้มเหลว
    """
    if not TTS_AVAILABLE:
        logger.error("pyttsx3 not available")
        return False
    
    if not text:
        return False
    
    try:
        logger.info(f"🔊 Speaking (simple): {text[:50]}...")
        
        # สร้าง engine ใหม่ทุกครั้ง (เหมือน test script)
        engine = pyttsx3.init()
        
        # ตั้งค่า
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        
        # ลองเลือก voice ที่ดีที่สุด
        try:
            voices = engine.getProperty('voices')
            if voices and len(voices) > 0:
                # ใช้ voice แรก
                engine.setProperty('voice', voices[0].id)
        except:
            pass
        
        # พูด (ใช้วิธีเดียวกับ test script)
        engine.say(text)
        engine.runAndWait()
        
        # ทำลาย engine
        del engine
        
        logger.info("✓ Speaking completed (simple)")
        return True
        
    except Exception as e:
        logger.error(f"Error in speak_simple: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


class SimpleTTS:
    """Simple TTS wrapper class"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.rate = self.config.get('rate', 180)
        self.volume = self.config.get('volume', 1.0)
        self.available = TTS_AVAILABLE
        self.is_speaking = False  # เพิ่ม flag
    
    def speak(self, text: str, blocking: bool = True):
        """พูดข้อความ"""
        self.is_speaking = True
        result = speak_simple(text, self.rate, self.volume)
        self.is_speaking = False
        return result
    
    def stop(self):
        """หยุดการพูด (ไม่ได้ implement)"""
        self.is_speaking = False
    
    def is_available_tts(self):
        """ตรวจสอบว่าพร้อมใช้งานหรือไม่"""
        return self.available
    
    def is_busy(self):
        """ตรวจสอบว่ากำลังพูดอยู่หรือไม่"""
        return self.is_speaking