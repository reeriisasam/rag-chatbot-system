import threading
from typing import Dict, Any, Optional
from loguru import logger

# ตรวจสอบว่ามี pyttsx3 หรือไม่
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("pyttsx3 not installed - TTS features disabled")

class TextToSpeech:
    """แปลงข้อความเป็นเสียง"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engine_name = config.get('engine', 'pyttsx3')
        self.rate = config.get('rate', 150)
        self.volume = config.get('volume', 0.9)
        self.voice = config.get('voice', 'th')
        
        self.engine = None
        self.is_speaking = False
        self.available = False
        
        if TTS_AVAILABLE:
            self._initialize_engine()
        else:
            logger.error("TTS not available - pyttsx3 not installed")
    
    def _initialize_engine(self):
        """สร้าง TTS engine"""
        try:
            if self.engine_name == 'pyttsx3':
                self.engine = pyttsx3.init()
                self._configure_pyttsx3()
                self.available = True
                logger.info("pyttsx3 TTS engine initialized")
            else:
                logger.warning(f"Unknown engine: {self.engine_name}, using pyttsx3")
                self.engine = pyttsx3.init()
                self._configure_pyttsx3()
                self.available = True
        except Exception as e:
            logger.error(f"Error initializing TTS engine: {e}")
            self.available = False
    
    def _configure_pyttsx3(self):
        """ตั้งค่า pyttsx3"""
        try:
            # ตั้งค่าความเร็ว
            self.engine.setProperty('rate', self.rate)
            
            # ตั้งค่าระดับเสียง
            self.engine.setProperty('volume', self.volume)
            
            # เลือกเสียง (ถ้ามี)
            voices = self.engine.getProperty('voices')
            if voices:
                # พยายามหาเสียงภาษาไทย
                thai_voice = None
                for voice in voices:
                    if 'thai' in voice.name.lower() or 'th' in voice.id.lower():
                        thai_voice = voice
                        break
                
                if thai_voice and self.voice == 'th':
                    self.engine.setProperty('voice', thai_voice.id)
                    logger.info(f"Using Thai voice: {thai_voice.name}")
                elif voices:
                    # ใช้เสียงแรก
                    self.engine.setProperty('voice', voices[0].id)
                    logger.info(f"Using default voice: {voices[0].name}")
            
        except Exception as e:
            logger.error(f"Error configuring pyttsx3: {e}")
    
    def speak(self, text: str, blocking: bool = True):
        """
        พูดข้อความ
        
        Args:
            text: ข้อความที่ต้องการพูด
            blocking: รอให้พูดจบก่อนคืนค่า (True) หรือไม่ (False)
        """
        if not text:
            return
        
        if not self.available or not self.engine:
            logger.warning("TTS not available")
            return
        
        try:
            self.is_speaking = True
            
            if blocking:
                self._speak_blocking(text)
            else:
                self._speak_non_blocking(text)
                
        except Exception as e:
            logger.error(f"Error in speak: {e}")
            self.is_speaking = False
    
    def _speak_blocking(self, text: str):
        """พูดแบบ blocking"""
        try:
            logger.info(f"🔊 Speaking: {text[:50]}...")
            
            # สร้าง engine ใหม่ทุกครั้งเพื่อป้องกันปัญหา thread
            if not TTS_AVAILABLE:
                logger.error("pyttsx3 not available")
                return
            
            import pyttsx3
            
            # สร้าง engine ใหม่
            temp_engine = pyttsx3.init()
            
            # ตั้งค่า
            temp_engine.setProperty('rate', self.rate)
            temp_engine.setProperty('volume', self.volume)
            
            # ลองเปลี่ยน voice ถ้ามีหลาย voice
            try:
                voices = temp_engine.getProperty('voices')
                if voices and len(voices) > 0:
                    # ใช้ voice แรก (ปกติจะชัดกว่า)
                    temp_engine.setProperty('voice', voices[0].id)
                    logger.info(f"Using voice: {voices[0].name}")
            except Exception as e:
                logger.warning(f"Could not set voice: {e}")
            
            # พูด - ใช้วิธีที่ชัดเจน
            logger.info("Saying text...")
            temp_engine.say(text)
            
            logger.info("Running and waiting...")
            temp_engine.runAndWait()
            
            # ทำลาย engine
            logger.info("Stopping engine...")
            temp_engine.stop()
            del temp_engine
            
            self.is_speaking = False
            logger.info("✓ Speaking completed successfully")
            
        except Exception as e:
            logger.error(f"Error in blocking speak: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.is_speaking = False
    
    def _speak_non_blocking(self, text: str):
        """พูดแบบ non-blocking (ใน thread แยก)"""
        def _speak_thread():
            try:
                logger.info(f"🔊 Speaking: {text[:50]}...")
                self.engine.say(text)
                self.engine.runAndWait()
                self.is_speaking = False
            except Exception as e:
                logger.error(f"Error in non-blocking speak: {e}")
                self.is_speaking = False
        
        thread = threading.Thread(target=_speak_thread)
        thread.daemon = True
        thread.start()
    
    def stop(self):
        """หยุดการพูด"""
        try:
            if self.engine and self.is_speaking:
                self.engine.stop()
                self.is_speaking = False
                logger.info("Speech stopped")
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")
    
    def set_rate(self, rate: int):
        """
        ตั้งค่าความเร็วในการพูด
        
        Args:
            rate: ความเร็ว (50-300, default: 150)
        """
        try:
            self.rate = max(50, min(300, rate))
            self.engine.setProperty('rate', self.rate)
            logger.info(f"Speech rate set to: {self.rate}")
        except Exception as e:
            logger.error(f"Error setting rate: {e}")
    
    def set_volume(self, volume: float):
        """
        ตั้งค่าระดับเสียง
        
        Args:
            volume: ระดับเสียง (0.0-1.0)
        """
        try:
            self.volume = max(0.0, min(1.0, volume))
            self.engine.setProperty('volume', self.volume)
            logger.info(f"Volume set to: {self.volume}")
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
    
    def get_voices(self) -> list:
        """ดึงรายการเสียงที่มี"""
        try:
            voices = self.engine.getProperty('voices')
            return [
                {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': voice.languages
                }
                for voice in voices
            ]
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []
    
    def set_voice(self, voice_id: str):
        """เปลี่ยนเสียง"""
        try:
            self.engine.setProperty('voice', voice_id)
            logger.info(f"Voice changed to: {voice_id}")
        except Exception as e:
            logger.error(f"Error setting voice: {e}")
    
    def save_to_file(self, text: str, filename: str):
        """
        บันทึกเสียงเป็นไฟล์
        
        Args:
            text: ข้อความที่ต้องการแปลง
            filename: ชื่อไฟล์ที่จะบันทึก
        """
        try:
            self.engine.save_to_file(text, filename)
            self.engine.runAndWait()
            logger.info(f"Speech saved to: {filename}")
        except Exception as e:
            logger.error(f"Error saving to file: {e}")
    
    def is_busy(self) -> bool:
        """เช็คว่ากำลังพูดอยู่หรือไม่"""
        return self.is_speaking
    
    def is_available_tts(self) -> bool:
        """ตรวจสอบว่า TTS พร้อมใช้งานหรือไม่"""
        return self.available and self.engine is not None