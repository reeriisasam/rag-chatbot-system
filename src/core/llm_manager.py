from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from loguru import logger
import requests

class LLMManager:
    """จัดการ LLM providers ต่างๆ (OpenAI, Llama, Custom Base URL)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get('provider', 'openai')
        self.llm = self._initialize_llm()
        
    def _initialize_llm(self):
        """สร้าง LLM instance ตาม provider ที่เลือก"""
        try:
            if self.provider == 'openai':
                return self._create_openai_llm()
            elif self.provider == 'llama':
                return self._create_llama_llm()
            elif self.provider == 'custom':
                return self._create_custom_llm()
            elif self.provider == 'donmi':
                return self._create_donmi_llm()
            else:
                logger.warning(f"Unknown provider: {self.provider}, using OpenAI as fallback")
                return self._create_openai_llm()
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise
    
    def _create_openai_llm(self):
        """สร้าง OpenAI LLM"""
        api_key = self.config.get('api_key')
        base_url = self.config.get('base_url')
        
        # ถ้ามี base_url แสดงว่าเป็น custom endpoint
        if base_url:
            logger.info(f"Using custom OpenAI-compatible endpoint: {base_url}")
            return ChatOpenAI(
                model=self.config.get('model_name', 'gpt-3.5-turbo'),
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', 2000),
                api_key=api_key or "dummy-key",
                base_url=base_url
            )
        else:
            # OpenAI ปกติ
            return ChatOpenAI(
                model=self.config.get('model_name', 'gpt-3.5-turbo'),
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', 2000),
                api_key=api_key
            )
    
    def _create_llama_llm(self):
        """สร้าง Llama LLM (local)"""
        try:
            from langchain_community.llms import LlamaCpp
            from langchain_core.callbacks import StreamingStdOutCallbackHandler
            
            model_path = self.config.get('llama_model_path')
            if not model_path:
                raise ValueError("llama_model_path not specified in config")
            
            return LlamaCpp(
                model_path=model_path,
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', 2000),
                n_ctx=2048,
                callbacks=[StreamingStdOutCallbackHandler()],
                verbose=False,
            )
        except ImportError:
            logger.error("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
            raise
    
    def _create_custom_llm(self):
        """สร้าง Custom LLM จาก base URL (Ollama, LocalAI, etc.)"""
        base_url = self.config.get('base_url')
        api_key = self.config.get('api_key', 'dummy-key')
        
        if not base_url:
            raise ValueError("base_url not specified in config")
        
        logger.info(f"Using custom endpoint: {base_url}")
        
        return ChatOpenAI(
            model=self.config.get('model_name', 'llama2'),
            temperature=self.config.get('temperature', 0.7),
            max_tokens=self.config.get('max_tokens', 2000),
            api_key=api_key,
            base_url=base_url
        )
    
    def _create_donmi_llm(self):
        """สร้าง Donmi Custom LLM (ไม่ใช้ LangChain wrapper)"""
        logger.info("Using Donmi custom API format")
        return None  # จะใช้ direct API call แทน
    
    def generate(
        self, 
        messages: List[BaseMessage],
        **kwargs
    ) -> str:
        """
        สร้างคำตอบจาก LLM
        
        Args:
            messages: รายการของ messages (HumanMessage, AIMessage, SystemMessage)
            **kwargs: พารามิเตอร์เพิ่มเติม
        
        Returns:
            คำตอบจาก LLM
        """
        try:
            # ถ้าเป็น Donmi provider ใช้ custom API call
            if self.provider == 'donmi':
                return self._call_donmi_api(messages, **kwargs)
            
            # ถ้าไม่ใช่ ใช้ LangChain ปกติ
            response = self.llm.invoke(messages, **kwargs)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"ขออภัย เกิดข้อผิดพลาด: {str(e)}"
    
    async def agenerate(
        self,
        messages: List[BaseMessage],
        **kwargs
    ) -> str:
        """Async version ของ generate"""
        try:
            # ถ้าเป็น Donmi provider ใช้ custom API call
            if self.provider == 'donmi':
                return self._call_donmi_api(messages, **kwargs)
            
            response = await self.llm.ainvoke(messages, **kwargs)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"ขออภัย เกิดข้อผิดพลาด: {str(e)}"
    
    def _call_donmi_api(self, messages: List[BaseMessage], **kwargs) -> str:
        """
        เรียก Donmi API แบบ custom format
        
        Args:
            messages: รายการของ messages
            **kwargs: พารามิเตอร์เพิ่มเติม
        
        Returns:
            คำตอบจาก API
        """
        try:
            # รวม messages เป็น prompt เดียว
            full_prompt = self._messages_to_prompt(messages)
            
            # ดึง config
            api_url = self.config.get('api_url') or self.config.get('base_url')
            api_key = self.config.get('api_key')
            timeout = self.config.get('timeout', 60)
            citation = self.config.get('citation', False)
            response_mode = self.config.get('response_mode', 'blocking')
            
            if not api_url:
                raise ValueError("api_url not specified in config")
            
            if not api_key:
                raise ValueError("api_key not specified in config")
            
            # สร้าง headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # สร้าง payload
            payload = {
                "inputs": {"question": full_prompt},
                "citation": citation,
                "response_mode": response_mode
            }
            
            logger.info(f"Calling Donmi API: {api_url}")
            logger.debug(f"Request payload: {payload}")
            
            # เรียก API พร้อม retry
            max_retries = 3
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempt {attempt + 1}/{max_retries}")
                    
                    response = requests.post(
                        api_url,
                        headers=headers,
                        json=payload,
                        timeout=timeout,
                        verify=False  # For development only
                    )
                    
                    # ตรวจสอบ status code
                    response.raise_for_status()
                    
                    # Parse response
                    result = response.json()
                    answer = result.get("answer", "ขออภัย ไม่สามารถตอบคำถามได้ในขณะนี้")
                    
                    logger.info("Donmi API response received successfully")
                    return answer
                    
                except requests.exceptions.Timeout:
                    last_error = f"Timeout: API ไม่ตอบกลับภายใน {timeout} วินาที"
                    logger.warning(f"{last_error} - Retry {attempt + 1}/{max_retries}")
                    
                except requests.exceptions.ConnectionError as e:
                    last_error = f"Connection Error: ไม่สามารถเชื่อมต่อไปยัง {api_url}"
                    logger.warning(f"{last_error} - Retry {attempt + 1}/{max_retries}")
                    logger.debug(f"Connection error details: {str(e)}")
                    
                except requests.exceptions.HTTPError as e:
                    status_code = e.response.status_code
                    if status_code == 401:
                        return "❌ API Key ไม่ถูกต้อง กรุณาตรวจสอบ API Key ในไฟล์ config"
                    elif status_code == 404:
                        return "❌ API URL ไม่ถูกต้อง กรุณาตรวจสอบ URL ในไฟล์ config"
                    elif status_code == 429:
                        last_error = "Rate limit exceeded - กรุณารอสักครู่"
                        logger.warning(last_error)
                    else:
                        last_error = f"HTTP {status_code}: {str(e)}"
                        logger.error(last_error)
                        return f"❌ เกิดข้อผิดพลาด: {last_error}"
                
                # รอก่อน retry (ยกเว้น attempt สุดท้าย)
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            
            # ถ้า retry หมดแล้วยังไม่สำเร็จ
            return f"❌ ไม่สามารถเชื่อมต่อ API ได้: {last_error}\n\nกรุณาตรวจสอบ:\n1. API URL ถูกต้องหรือไม่\n2. API Key ถูกต้องหรือไม่\n3. เชื่อมต่ออินเทอร์เน็ตหรือไม่"
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Configuration error: {error_msg}")
            return f"❌ การตั้งค่าไม่ถูกต้อง: {error_msg}"
            
        except Exception as e:
            logger.error(f"Unexpected error in Donmi API call: {e}")
            return f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {str(e)}"
    
    def _messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """
        แปลง messages เป็น prompt string
        
        Args:
            messages: รายการของ messages
        
        Returns:
            prompt string
        """
        prompt_parts = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                prompt_parts.append(f"System: {msg.content}")
            elif isinstance(msg, HumanMessage):
                prompt_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"Assistant: {msg.content}")
            else:
                prompt_parts.append(msg.content)
        
        return "\n\n".join(prompt_parts)
    
    def generate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        สร้างคำตอบพร้อม context จาก RAG
        
        Args:
            query: คำถามจากผู้ใช้
            context: ข้อมูล context จาก RAG
            system_prompt: System prompt (optional)
        
        Returns:
            คำตอบจาก LLM
        """
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        else:
            default_system = """คุณคือ AI Assistant ที่ชาญฉลาดและเป็นมิตร 
            ให้ตอบคำถามโดยใช้ข้อมูลจาก context ที่ให้มา 
            ถ้าไม่มีข้อมูลใน context ให้บอกตามตรงว่าไม่ทราบ
            ตอบเป็นภาษาไทยที่เป็นธรรมชาติและเข้าใจง่าย"""
            messages.append(SystemMessage(content=default_system))
        
        # เพิ่ม context
        user_message = f"""Context:
{context}

คำถาม: {query}

กรุณาตอบคำถามโดยอ้างอิงจาก context ด้านบน"""
        
        messages.append(HumanMessage(content=user_message))
        
        return self.generate(messages)
    
    def change_provider(self, provider: str, **kwargs):
        """เปลี่ยน LLM provider"""
        self.provider = provider
        self.config.update(kwargs)
        self.llm = self._initialize_llm()
        logger.info(f"Changed LLM provider to: {provider}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """ดึงข้อมูลของ model ปัจจุบัน"""
        return {
            'provider': self.provider,
            'model_name': self.config.get('model_name'),
            'temperature': self.config.get('temperature'),
            'max_tokens': self.config.get('max_tokens'),
        }