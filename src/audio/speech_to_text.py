import tempfile
import os
from typing import Optional, Dict, Any
from loguru import logger

# ตรวจสอบว่ามี speech_recognition หรือไม่
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    logger.warning("SpeechRecognition not installed")

# ตรวจสอบว่ามี PyAudio หรือไม่
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio not installed - microphone features will be disabled")

class SpeechToText:
    """แปลงเสียงเป็นข้อความ"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engine = config.get('engine', 'whisper')
        self.model = config.get('model', 'base')
        self.language = config.get('language', 'th')
        
        # ตรวจสอบว่ามี dependencies หรือไม่
        if not SR_AVAILABLE:
            logger.error("SpeechRecognition not installed. Install with: pip install SpeechRecognition")
            self.available = False
            return
        
        if not PYAUDIO_AVAILABLE:
            logger.error("PyAudio not installed. Microphone features disabled.")
            self.available = False
            return
        
        self.available = True
        self.recognizer = sr.Recognizer()
        
        # โหลด Whisper model ถ้าใช้
        self.whisper_model = None
        if self.engine == 'whisper':
            self._load_whisper()
    
    def _load_whisper(self):
        """โหลด Whisper model"""
        try:
            import whisper
            logger.info(f"Loading Whisper model: {self.model}")
            self.whisper_model = whisper.load_model(self.model)
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.warning("Whisper not installed. Install with: pip install openai-whisper")
            self.engine = 'google'
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            logger.info("Falling back to Google Speech Recognition")
            self.engine = 'google'
    
    def listen_from_microphone(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        ฟังเสียงจากไมโครโฟน
        
        Args:
            timeout: เวลารอก่อนเริ่มฟัง (วินาที)
            phrase_time_limit: เวลาสูงสุดในการพูด (วินาที)
        
        Returns:
            ข้อความที่แปลงได้ หรือ None ถ้าล้มเหลว
        """
        if not self.available:
            logger.error("Speech recognition not available - missing dependencies")
            return None
        
        if not SR_AVAILABLE:
            logger.error("SpeechRecognition not installed")
            return None
        
        if not PYAUDIO_AVAILABLE:
            logger.error("PyAudio not installed - cannot access microphone")
            return None
        
        try:
            with sr.Microphone() as source:
                logger.info("🎤 กำลังปรับระดับเสียง...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info("🎤 พูดได้เลย...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                logger.info("🎤 กำลังแปลงเสียง...")
                return self._transcribe(audio)
                
        except sr.WaitTimeoutError:
            logger.warning("Timeout: ไม่ได้ยินเสียง")
            return None
        except Exception as e:
            logger.error(f"Error listening from microphone: {e}")
            return None
    
    def transcribe_file(self, audio_file_path: str) -> Optional[str]:
        """
        แปลงไฟล์เสียงเป็นข้อความ
        
        Args:
            audio_file_path: path ของไฟล์เสียง
        
        Returns:
            ข้อความที่แปลงได้
        """
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
                return self._transcribe(audio)
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            return None
    
    def _transcribe(self, audio) -> Optional[str]:
        """
        แปลงเสียงเป็นข้อความด้วย engine ที่เลือก
        
        Args:
            audio: AudioData object
        
        Returns:
            ข้อความที่แปลงได้
        """
        try:
            if self.engine == 'whisper' and self.whisper_model:
                return self._transcribe_whisper(audio)
            elif self.engine == 'google':
                return self._transcribe_google(audio)
            else:
                logger.warning(f"Unknown engine: {self.engine}, using Google")
                return self._transcribe_google(audio)
                
        except Exception as e:
            logger.error(f"Error in transcription: {e}")
            return None
    
    def _transcribe_whisper(self, audio) -> Optional[str]:
        """แปลงด้วย Whisper"""
        try:
            # บันทึก audio เป็นไฟล์ชั่วคราว
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio.get_wav_data())
                temp_file = f.name
            
            try:
                # ใช้ Whisper แปลง
                result = self.whisper_model.transcribe(
                    temp_file,
                    language=self.language
                )
                return result['text'].strip()
            finally:
                # ลบไฟล์ชั่วคราว
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as e:
            logger.error(f"Error in Whisper transcription: {e}")
            return None
    
    def _transcribe_google(self, audio) -> Optional[str]:
        """แปลงด้วย Google Speech Recognition"""
        try:
            language_code = 'th-TH' if self.language == 'th' else 'en-US'
            text = self.recognizer.recognize_google(
                audio,
                language=language_code
            )
            return text.strip()
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition ไม่เข้าใจเสียงที่พูด")
            return None
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition error: {e}")
            return None
    
    def set_language(self, language: str):
        """เปลี่ยนภาษา"""
        self.language = language
        logger.info(f"Language changed to: {language}")
    
    def set_engine(self, engine: str):
        """เปลี่ยน engine"""
        self.engine = engine
        if engine == 'whisper' and not self.whisper_model:
            self._load_whisper()
        logger.info(f"Engine changed to: {engine}")
    
    def test_microphone(self) -> bool:
        """ทดสอบไมโครโฟน"""
        if not self.available:
            logger.error("Speech recognition not available")
            return False
        
        if not PYAUDIO_AVAILABLE:
            logger.error("PyAudio not installed - cannot test microphone")
            return False
        
        try:
            with sr.Microphone() as source:
                logger.info("Testing microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("✓ Microphone is working")
                return True
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """ตรวจสอบว่า speech recognition พร้อมใช้งานหรือไม่"""
        return self.available and SR_AVAILABLE and PYAUDIO_AVAILABLE