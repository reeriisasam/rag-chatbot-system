#!/usr/bin/env python3
"""
RAG Chatbot System
โปรแกรม Chatbot ที่รวม RAG, LLM และการสนทนาด้วยเสียง
"""

import sys
from pathlib import Path
from loguru import logger

# เพิ่ม src ไปยัง path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import get_config
from src.core.llm_manager import LLMManager
from src.core.vector_store import VectorStoreManager
from src.rag.document_loader import DocumentLoader
from src.rag.retriever import RAGRetriever
from src.graph.workflow import RAGChatWorkflow
from src.ui.terminal_ui import TerminalUI
from langchain_core.messages import BaseMessage

# Audio components (optional)
try:
    from src.audio.speech_to_text import SpeechToText
    from src.audio.text_to_speech import TextToSpeech
    AUDIO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Audio features not available: {e}")
    AUDIO_AVAILABLE = False
    SpeechToText = None
    TextToSpeech = None


class RAGChatbot:
    """Main Chatbot Application"""
    
    def __init__(self):
        logger.info("Initializing RAG Chatbot System...")
        
        # โหลด config
        self.config = get_config()
        
        # สร้าง components
        self._initialize_components()
        
        # ประวัติการสนทนา
        self.conversation_history = []
        
        logger.info("RAG Chatbot System initialized successfully!")
    
    def _initialize_components(self):
        """สร้าง components ทั้งหมด"""
        try:
            # UI
            self.ui = TerminalUI(self.config.get('ui', {}))
            
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
            else:
                self.stt = None
                self.tts = None
                logger.warning("Audio features disabled - install required packages to enable")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def load_documents(self):
        """โหลดเอกสารเข้าระบบ"""
        doc_dir = self.config.get('documents.directory', './data/documents')
        
        if not Path(doc_dir).exists():
            logger.warning(f"Document directory not found: {doc_dir}")
            return False
        
        self.ui.show_info("กำลังโหลดเอกสาร...")
        
        try:
            # โหลดเอกสาร
            documents = self.doc_loader.load_directory(doc_dir)
            
            if not documents:
                self.ui.show_info("ไม่พบเอกสารในโฟลเดอร์")
                return False
            
            # เพิ่มเข้า vector store
            success = self.vector_store.add_documents(documents)
            
            if success:
                self.ui.show_success(f"โหลดเอกสารสำเร็จ: {len(documents)} chunks")
            else:
                self.ui.show_error("เกิดข้อผิดพลาดในการโหลดเอกสาร")
            
            return success
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            self.ui.show_error(f"เกิดข้อผิดพลาด: {str(e)}")
            return False
    
    def handle_text_input(self):
        """จัดการ input แบบข้อความ"""
        user_input = self.ui.get_input()
        
        if not user_input:
            return True
        
        # เช็คคำสั่งพิเศษ
        if user_input.lower() in ['exit', 'quit']:
            return False
        
        if user_input.startswith('/'):
            return self.handle_command(user_input)
        
        # ประมวลผลคำถาม
        self.process_query(user_input, mode='text')
        return True
    
    def handle_voice_input(self):
        """จัดการ input แบบเสียง"""
        if not AUDIO_AVAILABLE or not self.stt or not self.tts:
            self.ui.show_error("ฟีเจอร์เสียงยังไม่พร้อมใช้งาน กรุณาติดตั้ง: pip install SpeechRecognition pyttsx3 pyaudio torch")
            self.ui.set_mode('text')
            return True
        
        self.ui.show_listening()
        
        # ฟังเสียงจากไมโครโฟน
        text = self.stt.listen_from_microphone()
        
        if not text:
            self.ui.show_error("ไม่สามารถแปลงเสียงได้")
            return True
        
        # แสดงข้อความที่ได้
        self.ui.show_message('user', text)
        
        # เช็คคำสั่ง
        if text.lower() in ['ออก', 'exit', 'quit', 'ปิด']:
            return False
        
        # ประมวลผลคำถาม
        self.process_query(text, mode='voice')
        return True
    
    def process_query(self, query: str, mode: str = 'text'):
        """
        ประมวลผลคำถามและสร้างคำตอบ
        
        Args:
            query: คำถามจากผู้ใช้
            mode: โหมด ('text' หรือ 'voice')
        """
        self.ui.show_thinking()
        
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
            
            self.ui.show_message('assistant', response, metadata)
            
            # ถ้าเป็นโหมดเสียง ให้อ่านคำตอบออกมา
            if mode == 'voice' and AUDIO_AVAILABLE and self.tts:
                self.tts.speak(response, blocking=True)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            self.ui.show_error(f"เกิดข้อผิดพลาด: {str(e)}")
    
    def handle_command(self, command: str) -> bool:
        """
        จัดการคำสั่งพิเศษ
        
        Args:
            command: คำสั่ง
        
        Returns:
            True ถ้าจะทำต่อ, False ถ้าจะออก
        """
        command = command.lower().strip()
        
        if command == '/help':
            self.ui.show_help()
        
        elif command == '/clear':
            self.ui.clear()
        
        elif command == '/stats':
            stats = self.get_system_stats()
            self.ui.show_stats(stats)
        
        elif command.startswith('/mode '):
            mode = command.split()[1]
            if mode in ['text', 'voice']:
                if mode == 'voice' and not AUDIO_AVAILABLE:
                    self.ui.show_error("ฟีเจอร์เสียงยังไม่พร้อมใช้งาน")
                    self.ui.show_info("ติดตั้งด้วย: pip install SpeechRecognition pyttsx3 pyaudio torch")
                else:
                    self.ui.set_mode(mode)
            else:
                self.ui.show_error("โหมดไม่ถูกต้อง ใช้ 'text' หรือ 'voice'")
        
        elif command == '/reload':
            self.load_documents()
        
        else:
            self.ui.show_error(f"ไม่รู้จักคำสั่ง: {command}")
            self.ui.show_info("พิมพ์ /help เพื่อดูคำสั่งที่ใช้ได้")
        
        return True
    
    def get_system_stats(self) -> dict:
        """ดึงสถิติระบบ"""
        vector_stats = self.vector_store.get_stats()
        llm_info = self.llm_manager.get_model_info()
        
        stats = {
            'LLM Provider': llm_info['provider'],
            'Model': llm_info['model_name'],
            'Vector Store': vector_stats['type'],
            'Documents': vector_stats.get('count', 0),
            'Conversation Length': len(self.conversation_history),
            'Mode': self.ui.get_mode(),
            'Audio Features': 'Enabled' if AUDIO_AVAILABLE else 'Disabled'
        }
        
        return stats
    
    def run(self):
        """เริ่มต้นโปรแกรม"""
        try:
            # แสดงหน้าจอต้อนรับ
            self.ui.show_welcome()
            
            # ถามว่าจะโหลดเอกสารหรือไม่
            self.ui.show_info("ต้องการโหลดเอกสารเข้าระบบหรือไม่? (y/n)")
            choice = self.ui.get_input("คำตอบ")
            
            if choice.lower() in ['y', 'yes', 'ใช่']:
                self.load_documents()
            
            # เริ่ม main loop
            while True:
                mode = self.ui.get_mode()
                
                try:
                    if mode == 'text':
                        if not self.handle_text_input():
                            break
                    else:  # voice
                        if not self.handle_voice_input():
                            break
                
                except KeyboardInterrupt:
                    self.ui.show_info("\nกด Ctrl+C อีกครั้งเพื่อออก")
                    continue
                
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    self.ui.show_error(f"เกิดข้อผิดพลาด: {str(e)}")
            
            # แสดงข้อความลาก่อน
            self.ui.show_goodbye()
            
        except KeyboardInterrupt:
            self.ui.show_goodbye()
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.ui.show_error(f"เกิดข้อผิดพลาดร้ายแรง: {str(e)}")
            sys.exit(1)


def main():
    """Entry point"""
    try:
        # สร้าง directories ที่จำเป็น
        Path("data/documents").mkdir(parents=True, exist_ok=True)
        Path("data/vector_db").mkdir(parents=True, exist_ok=True)
        Path("data/audio_cache").mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(parents=True, exist_ok=True)
        
        # เริ่มต้น chatbot
        chatbot = RAGChatbot()
        chatbot.run()
        
    except Exception as e:
        logger.error(f"Error starting chatbot: {e}")
        print(f"\n❌ เกิดข้อผิดพลาด: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()