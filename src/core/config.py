import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any
from loguru import logger

# โหลด environment variables
load_dotenv()

class Config:
    """จัดการ configuration ทั้งหมดของระบบ"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._setup_logging()
        
    def _load_config(self) -> Dict[str, Any]:
        """โหลด configuration จากไฟล์ YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Override with environment variables
            self._override_with_env(config)
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _override_with_env(self, config: Dict[str, Any]):
        """Override config ด้วย environment variables"""
        # Provider
        if os.getenv("LLM_PROVIDER"):
            config['llm']['provider'] = os.getenv("LLM_PROVIDER")
        
        # API Keys
        if os.getenv("OPENAI_API_KEY"):
            config['llm']['api_key'] = os.getenv("OPENAI_API_KEY")
        
        if os.getenv("LLM_API_KEY"):
            config['llm']['api_key'] = os.getenv("LLM_API_KEY")
        
        # Base URL / API URL
        if os.getenv("LLM_BASE_URL"):
            config['llm']['base_url'] = os.getenv("LLM_BASE_URL")
        
        if os.getenv("LLM_API_URL"):
            config['llm']['api_url'] = os.getenv("LLM_API_URL")
        
        # Model name
        if os.getenv("LLM_MODEL"):
            config['llm']['model_name'] = os.getenv("LLM_MODEL")
        
        # Temperature
        if os.getenv("LLM_TEMPERATURE"):
            try:
                config['llm']['temperature'] = float(os.getenv("LLM_TEMPERATURE"))
            except ValueError:
                pass
        
        # Max tokens
        if os.getenv("LLM_MAX_TOKENS"):
            try:
                config['llm']['max_tokens'] = int(os.getenv("LLM_MAX_TOKENS"))
            except ValueError:
                pass
        
        # Donmi-specific settings
        if os.getenv("LLM_TIMEOUT"):
            try:
                config['llm']['timeout'] = int(os.getenv("LLM_TIMEOUT"))
            except ValueError:
                pass
        
        if os.getenv("LLM_CITATION"):
            config['llm']['citation'] = os.getenv("LLM_CITATION").lower() == 'true'
        
        if os.getenv("LLM_RESPONSE_MODE"):
            config['llm']['response_mode'] = os.getenv("LLM_RESPONSE_MODE")
    
    def _setup_logging(self):
        """ตั้งค่า logging"""
        log_config = self.config.get('logging', {})
        log_file = log_config.get('file', './logs/app.log')
        log_level = log_config.get('level', 'INFO')
        
        # สร้าง logs directory
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # ลบ handler เก่าทั้งหมด
        logger.remove()
        
        # เพิ่ม handler ใหม่สำหรับ console
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        # เพิ่ม handler สำหรับไฟล์
        logger.add(
            log_file,
            rotation="500 MB",
            retention="10 days",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
        )
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'llm': {
                'provider': 'openai',
                'model_name': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'max_tokens': 2000
            },
            'rag': {
                'chunk_size': 1000,
                'chunk_overlap': 200,
                'top_k': 5
            },
            'audio': {
                'stt': {'engine': 'whisper', 'model': 'base'},
                'tts': {'engine': 'pyttsx3'}
            },
            'ui': {
                'mode': 'auto'
            }
        }
    
    def get(self, key_path: str, default=None):
        """
        ดึงค่า config โดยใช้ dot notation
        Example: config.get('llm.model_name')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key_path: str, value: Any):
        """ตั้งค่า config โดยใช้ dot notation"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self):
        """บันทึก config กลับไปที่ไฟล์"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

# Singleton instance
_config_instance = None

def get_config() -> Config:
    """ดึง Config instance (Singleton pattern)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance