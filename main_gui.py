#!/usr/bin/env python3
"""
RAG Chatbot System - GUI Version
โปรแกรม Chatbot แบบ GUI Window (เหมือน OpenCV)
"""

import sys
from pathlib import Path
from loguru import logger
import threading

# เพิ่ม src ไปยัง path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import get_config
from src.core.llm_manager import LLMManager
from src.core.vector_store import VectorStoreManager
from src.rag.document_loader import DocumentLoader
from src.rag.retriever import RAGRetriever
from src.graph.workflow import RAGChatWorkflow
from src.ui.gui_window import ChatGUI
from langchain_core.messages import BaseMessage

# Audio components (optional)
try:
    from src.audio.speech_to_text import SpeechToText
    # ใช้ SimpleTTS แทน TextToSpeech
    from src.audio.simple_tts import SimpleTTS as TextToSpeech
    AUDIO_AVAILABLE = True
    logger.info("Using SimpleTTS (tested and working)")
except ImportError as e:
    logger.warning(f"Audio features not available: {e}")
    AUDIO_AVAILABLE = False
    SpeechToText = None
    TextToSpeech = None


class RAGChatbotGUI:
    """Main Chatbot Application with GUI"""
    
    def __init__(self):
        logger.info("Initializing RAG Chatbot System (GUI)...")
        
        # โหลด config
        self.config = get_config()
        
        # สร้าง GUI
        self.gui = ChatGUI(title="🤖 RAG Chatbot System", config=self.config.config)
        
        # สร้าง components
        self._initialize_components()
        
        # ประวัติการสนทนา
        self.conversation_history = []
        
        # Voice mode state
        self.voice_conversation_active = False
        self.voice_thread = None
        
        # ตั้งค่า callbacks
        self._setup_callbacks()
        
        logger.info("RAG Chatbot System initialized successfully!")
    
    def _initialize_components(self):
        """สร้าง components ทั้งหมด"""
        try:
            # LLM
            self.llm_manager = LLMManager(self.config.get('llm', {}))
            
            # Vector Store
            vector_config = self.config.get('rag.vector_store', {})
            vector_config['embeddings'] = self.config.get('rag.embeddings', {})
            self.vector_store = VectorStoreManager(vector_config)
            
            # Document Loader
            self.doc_loader = DocumentLoader(self.config.get('rag', {}))
            
            # Retriever
            self.retriever = RAGRetriever(
                self.vector_store,
                self.config.get('rag', {})
            )
            
            # LangGraph Workflow
            self.workflow = RAGChatWorkflow(
                self.llm_manager,
                self.retriever
            )
            
            # Audio components
            if AUDIO_AVAILABLE:
                audio_config = self.config.get('audio', {})
                self.stt = SpeechToText(audio_config.get('stt', {}))
                self.tts = TextToSpeech(audio_config.get('tts', {}))
                
                # ตรวจสอบว่า STT พร้อมใช้งานหรือไม่
                if hasattr(self.stt, 'is_available') and not self.stt.is_available():
                    logger.warning("Speech-to-Text not fully available")
                    self.gui.add_system_message("⚠️ โหมดเสียงไม่พร้อมใช้งาน - ขาด PyAudio\nติดตั้งด้วย: pip install pyaudio")
                    # ปิด voice mode
                    self.gui.voice_button.config(state='disabled')
            else:
                self.stt = None
                self.tts = None
                logger.warning("Audio features disabled")
                self.gui.add_system_message("⚠️ ฟีเจอร์เสียงไม่พร้อมใช้งาน - ขาด audio packages")
            
            self.gui.add_system_message("✅ ระบบพร้อมใช้งาน!")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            self.gui.show_error(f"เกิดข้อผิดพลาดในการเริ่มต้นระบบ: {str(e)}")
            raise
    
    def _setup_callbacks(self):
        """ตั้งค่า GUI callbacks"""
        self.gui.set_send_callback(self.handle_text_message)
        self.gui.set_voice_callback(self.handle_voice_message)
        self.gui.set_close_callback(self.on_close)
        self.gui.set_stats_callback(self.show_stats)
        
        # ตั้งค่า stop speaking callback ถ้า GUI รองรับ
        if hasattr(self.gui, 'set_stop_speaking_callback'):
            self.gui.set_stop_speaking_callback(self.stop_speaking)
    
    def load_documents(self):
        """โหลดเอกสารเข้าระบบ"""
        doc_dir = self.config.get('documents.directory', './data/documents')
        
        if not Path(doc_dir).exists():
            logger.warning(f"Document directory not found: {doc_dir}")
            return False
        
        self.gui.add_system_message("กำลังโหลดเอกสาร...")
        
        try:
            # โหลดเอกสาร
            documents = self.doc_loader.load_directory(doc_dir)
            
            if not documents:
                self.gui.add_system_message("ไม่พบเอกสารในโฟลเดอร์")
                return False
            
            # เพิ่มเข้า vector store
            success = self.vector_store.add_documents(documents)
            
            if success:
                self.gui.add_system_message(f"✅ โหลดเอกสารสำเร็จ: {len(documents)} chunks")
            else:
                self.gui.add_system_message("❌ เกิดข้อผิดพลาดในการโหลดเอกสาร")
            
            return success
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            self.gui.show_error(f"เกิดข้อผิดพลาด: {str(e)}")
            return False
    
    def handle_text_message(self, message: str):
        """จัดการข้อความจากผู้ใช้"""
        if not message:
            return
        
        # เช็คคำสั่งพิเศษ
        if message.startswith('/'):
            self.handle_command(message)
            return
        
        # แสดงข้อความของ user
        self.gui.add_user_message(message)
        
        # ประมวลผลคำถาม
        self.process_query(message, mode='text')
    
    def handle_voice_message(self):
        """จัดการ input แบบเสียง"""
        # ตรวจสอบว่า audio พร้อมใช้งานหรือไม่
        if not AUDIO_AVAILABLE:
            self._show_audio_install_guide()
            return
        
        if not self.stt or not self.tts:
            self._show_audio_install_guide()
            return
        
        # ตรวจสอบว่า STT พร้อมใช้งานหรือไม่
        if hasattr(self.stt, 'is_available') and not self.stt.is_available():
            self._show_audio_install_guide()
            return
        
        # เช็คว่ากำลัง active อยู่หรือไม่
        if self.voice_conversation_active:
            # ถ้ากำลัง active อยู่ ให้หยุด
            self.stop_voice_conversation()
        else:
            # เริ่ม voice conversation loop
            self.start_voice_conversation()
    
    def start_voice_conversation(self):
        """เริ่ม conversation loop แบบเสียง"""
        self.voice_conversation_active = True
        self.gui.add_system_message("🎤 เริ่มโหมดสนทนาเสียง - พูดได้เลย (พูด 'หยุด' หรือ 'ออก' เพื่อจบการสนทนา)")
        self.gui.voice_button.config(text="⏹️ Stop Voice")
        
        # รันใน thread แยก
        self.voice_thread = threading.Thread(target=self._voice_conversation_loop, daemon=True)
        self.voice_thread.start()
    
    def stop_voice_conversation(self):
        """หยุด conversation loop"""
        self.voice_conversation_active = False
        self.gui.voice_button.config(text="🎤 Voice")
        self.gui.hide_voice_indicator()
        self.gui.add_system_message("⏹️ หยุดโหมดสนทนาเสียงแล้ว")
    
    def _voice_conversation_loop(self):
        """Loop สำหรับสนทนาแบบเสียงต่อเนื่อง"""
        while self.voice_conversation_active:
            try:
                # แสดงสถานะฟัง
                self.gui.show_voice_indicator("🎤 กำลังฟัง...")
                logger.info("Listening for voice input...")
                
                # ฟังเสียงจากไมโครโฟน
                text = self.stt.listen_from_microphone(timeout=10, phrase_time_limit=10)
                
                if not text:
                    self.gui.hide_voice_indicator()
                    logger.info("No speech detected, continuing...")
                    continue
                
                # แสดงข้อความที่ได้
                logger.info(f"User said: {text}")
                self.gui.add_user_message(text)
                self.gui.hide_voice_indicator()
                
                # เช็คคำสั่งหยุด
                stop_words = ['หยุด', 'ออก', 'จบ', 'stop', 'exit', 'quit', 'ปิด']
                if any(word in text.lower() for word in stop_words):
                    logger.info("Stop command detected")
                    self.stop_voice_conversation()
                    break
                
                # ประมวลผลและตอบกลับ
                logger.info("Processing query...")
                self.process_query(text, mode='voice')
                
                # **รอให้พูดจบก่อน** โดยเช็ค flag
                logger.info("Waiting for TTS to complete...")
                import time
                
                max_wait = 30  # รอสูงสุด 30 วินาที
                waited = 0
                sleep_interval = 0.2  # เช็คทุก 0.2 วินาที
                
                while waited < max_wait:
                    # เช็คว่า TTS ยังพูดอยู่หรือไม่
                    if self.tts and hasattr(self.tts, 'is_busy'):
                        if not self.tts.is_busy():
                            logger.info("TTS completed speaking")
                            break
                    else:
                        # ถ้าไม่มี is_busy ให้ดูจาก indicator
                        if not self.gui.voice_indicator.cget('text'):
                            break
                    
                    time.sleep(sleep_interval)
                    waited += sleep_interval
                
                # รอเพิ่มอีก 0.5 วินาทีก่อนฟังใหม่ (ให้แน่ใจว่าจบแล้ว)
                time.sleep(0.5)
                logger.info("Ready for next input")
                
            except Exception as e:
                logger.error(f"Error in voice conversation loop: {e}")
                import traceback
                logger.error(traceback.format_exc())
                self.gui.hide_voice_indicator()
                self.gui.add_system_message(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                break
    
    def _show_audio_install_guide(self):
        """แสดงคำแนะนำการติดตั้ง audio packages"""
        guide = """❌ ฟีเจอร์เสียงไม่พร้อมใช้งาน

สาเหตุ: ขาด PyAudio หรือ audio packages

📦 วิธีติดตั้ง:

Windows:
  pip install pipwin
  pipwin install pyaudio
  pip install SpeechRecognition pyttsx3

Linux:
  sudo apt-get install portaudio19-dev python3-pyaudio
  pip install pyaudio SpeechRecognition pyttsx3

macOS:
  brew install portaudio
  pip install pyaudio SpeechRecognition pyttsx3

หลังติดตั้งเสร็จ รีสตาร์ทโปรแกรม"""
        
        self.gui.add_system_message(guide)
    
    def process_query(self, query: str, mode: str = 'text'):
        """ประมวลผลคำถามและสร้างคำตอบ"""
        self.gui.set_processing(True)
        
        try:
            # รัน workflow
            result = self.workflow.run(
                query=query,
                messages=self.conversation_history,
                mode=mode
            )
            
            response = result['response']
            self.conversation_history = result['messages']
            
            # แสดงคำตอบ
            metadata = {
                'use_rag': result.get('use_rag', False)
            }
            
            self.gui.add_bot_message(response, metadata)
            
            # ถ้าเป็นโหมดเสียง ให้อ่านคำตอบออกมา
            if mode == 'voice':
                # ใช้ after เพื่อไม่ block UI
                self.gui.root.after(100, lambda: self._speak_response(response))
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            self.gui.show_error(f"เกิดข้อผิดพลาด: {str(e)}")
        
        finally:
            self.gui.set_processing(False)
    
    def _speak_response(self, text: str):
        """พูดคำตอบออกมาเป็นเสียง"""
        if not AUDIO_AVAILABLE or not self.tts:
            logger.warning("TTS not available")
            return
        
        # เช็คว่า TTS พร้อมใช้งานหรือไม่
        if hasattr(self.tts, 'is_available_tts') and not self.tts.is_available_tts():
            logger.warning("TTS engine not initialized")
            self.gui.add_system_message("⚠️ ระบบเสียงไม่พร้อมใช้งาน")
            return
        
        try:
            logger.info("🔊 Starting to speak...")
            
            # แสดงสถานะ
            self.gui.show_voice_indicator("🔊 กำลังพูด...")
            
            # ตัดข้อความที่ยาวเกินไป
            max_length = 500
            if len(text) > max_length:
                speak_text = text[:max_length] + "..."
                logger.info(f"Text truncated from {len(text)} to {max_length} chars")
            else:
                speak_text = text
            
            logger.info(f"Speaking text: {speak_text[:50]}...")
            
            # พูดโดยตรง ไม่ใช้ thread (แก้ปัญหา pyttsx3)
            try:
                self.tts.speak(speak_text, blocking=True)
                logger.info("✓ Speaking completed successfully")
            except Exception as e:
                logger.error(f"Error speaking: {e}")
                self.gui.add_system_message(f"❌ เกิดข้อผิดพลาดในการพูด: {str(e)}")
            finally:
                # ซ่อนสถานะ
                self.gui.hide_voice_indicator()
            
        except Exception as e:
            logger.error(f"Error in speak response: {e}")
            self.gui.hide_voice_indicator()
    
    def handle_command(self, command: str):
        """จัดการคำสั่งพิเศษ"""
        command = command.lower().strip()
        
        if command == '/help':
            help_text = """คำสั่งที่ใช้ได้:
  /help    - แสดงคำสั่งนี้
  /clear   - ล้างหน้าจอ
  /stats   - แสดงสถิติระบบ
  /reload  - โหลดเอกสารใหม่
  /mode    - สลับโหมด text/voice
  /test    - ทดสอบการเชื่อมต่อ API"""
            self.gui.add_system_message(help_text)
        
        elif command == '/clear':
            self.gui.clear_chat()
        
        elif command == '/stats':
            self.show_stats()
        
        elif command == '/reload':
            threading.Thread(target=self.load_documents, daemon=True).start()
        
        elif command == '/mode':
            self.gui.toggle_mode()
        
        elif command == '/test':
            self.test_api_connection()
        
        else:
            self.gui.add_system_message(f"❌ ไม่รู้จักคำสั่ง: {command}\nพิมพ์ /help เพื่อดูคำสั่งที่ใช้ได้")
    
    def show_stats(self):
        """แสดงสถิติระบบ"""
        try:
            vector_stats = self.vector_store.get_stats()
            llm_info = self.llm_manager.get_model_info()
            
            stats_text = f"""📊 สถิติระบบ
{'─' * 50}
LLM Provider:        {llm_info['provider']}
Model:               {llm_info['model_name']}
Temperature:         {llm_info['temperature']}
Vector Store:        {vector_stats['type']}
Documents:           {vector_stats.get('count', 0)} chunks
Conversation:        {len(self.conversation_history)} messages
Audio Features:      {'Enabled' if AUDIO_AVAILABLE else 'Disabled'}
Mode:                {self.gui.current_mode}
"""
            self.gui.add_system_message(stats_text)
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            self.gui.show_error(f"เกิดข้อผิดพลาด: {str(e)}")
    
    def test_api_connection(self):
        """ทดสอบการเชื่อมต่อ API"""
        self.gui.add_system_message("🔍 กำลังทดสอบการเชื่อมต่อ API...")
        self.gui.set_processing(True)
        
        def _test():
            try:
                from langchain_core.messages import HumanMessage
                
                # ส่งข้อความทดสอบ
                test_message = [HumanMessage(content="test")]
                result = self.llm_manager.generate(test_message)
                
                if "❌" in result or "error" in result.lower():
                    self.gui.add_system_message(f"❌ การทดสอบล้มเหลว:\n{result}")
                else:
                    self.gui.add_system_message(f"✅ การทดสอบสำเร็จ!\n\nคำตอบจาก API: {result[:100]}...")
                
            except Exception as e:
                self.gui.add_system_message(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            finally:
                self.gui.set_processing(False)
        
        threading.Thread(target=_test, daemon=True).start()
    
    def on_close(self):
        """เรียกเมื่อปิดโปรแกรม"""
        logger.info("Closing RAG Chatbot System...")
        # หยุด voice conversation ถ้ากำลังทำงาน
        self.voice_conversation_active = False
        # หยุดการพูดถ้ากำลังพูดอยู่
        self.stop_speaking()
        # ทำความสะอาด resources ถ้ามี
    
    def stop_speaking(self):
        """หยุดการพูด"""
        if AUDIO_AVAILABLE and self.tts:
            try:
                self.tts.stop()
                logger.info("Speech stopped")
            except Exception as e:
                logger.error(f"Error stopping speech: {e}")
        
    def run(self):
        """เริ่มต้นโปรแกรม"""
        try:
            # ถามว่าจะโหลดเอกสารหรือไม่
            self.gui.add_system_message("ต้องการโหลดเอกสารเข้าระบบหรือไม่? (พิมพ์ 'y' หรือ 'yes')")
            
            # เริ่ม GUI
            self.gui.run()
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)


def main():
    """Entry point"""
    try:
        # สร้าง directories ที่จำเป็น
        Path("data/documents").mkdir(parents=True, exist_ok=True)
        Path("data/vector_db").mkdir(parents=True, exist_ok=True)
        Path("data/audio_cache").mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(parents=True, exist_ok=True)
        
        # เริ่มต้น chatbot GUI
        chatbot = RAGChatbotGUI()
        
        # โหลดเอกสารอัตโนมัติถ้ามี
        if Path("data/documents").exists() and any(Path("data/documents").iterdir()):
            threading.Thread(target=chatbot.load_documents, daemon=True).start()
        
        chatbot.run()
        
    except Exception as e:
        logger.error(f"Error starting chatbot: {e}")
        print(f"\n❌ เกิดข้อผิดพลาด: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()