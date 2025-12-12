# 🤖 RAG Chatbot System

ระบบ Chatbot ที่มีความสามารถในการตอบคำถามด้วย RAG (Retrieval Augmented Generation) พร้อมรองรับการสนทนาทั้งแบบข้อความและเสียง โดยใช้ LangGraph ในการจัดการ workflow

## ✨ Features

- 🔍 **RAG System** - ค้นหาข้อมูลจากเอกสารและตอบคำถามอย่างแม่นยำ
- 🧠 **Multiple LLM Support** - รองรับ OpenAI, Llama (local), และ Custom API (Ollama, LocalAI)
- 🎙️ **Voice Interaction** - สนทนาด้วยเสียงได้ทั้งพูดและฟัง
- 💬 **Text Chat** - สนทนาแบบข้อความในรูปแบบ terminal ที่สวยงาม
- 📚 **Document Loading** - รองรับ PDF, DOCX, TXT, Markdown
- 🔄 **LangGraph Workflow** - จัดการ flow การสนทนาอย่างมีประสิทธิภาพ
- 💾 **Vector Store** - ใช้ ChromaDB หรือ FAISS สำหรับเก็บข้อมูล

## 📁 โครงสร้างโปรเจค

```
rag-chatbot-system/
├── main.py                    # จุดเริ่มต้นโปรแกรม
├── config.yaml               # การตั้งค่าระบบ
├── requirements.txt          # Dependencies
├── .env.example             # ตัวอย่าง environment variables
│
├── src/
│   ├── core/                # Core components
│   │   ├── config.py
│   │   ├── llm_manager.py
│   │   └── vector_store.py
│   │
│   ├── rag/                 # RAG system
│   │   ├── document_loader.py
│   │   ├── embeddings.py
│   │   └── retriever.py
│   │
│   ├── graph/              # LangGraph workflow
│   │   ├── nodes.py
│   │   └── workflow.py
│   │
│   ├── audio/              # Audio processing
│   │   ├── speech_to_text.py
│   │   └── text_to_speech.py
│   │
│   └── ui/                 # User interface
│       ├── terminal_ui.py
│       └── chat_handler.py
│
└── data/
    ├── documents/          # วางเอกสารที่นี่
    ├── vector_db/          # Vector database storage
    └── audio_cache/        # Cache ไฟล์เสียง
```

## 🚀 การติดตั้ง

### 1. Clone โปรเจค

```bash
git clone <repository-url>
cd rag-chatbot-system
```

### 2. สร้าง Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 4. ตั้งค่า Environment Variables

```bash
cp .env.example .env
# แก้ไข .env และใส่ API key ของคุณ
```

### 5. แก้ไข config.yaml

แก้ไขไฟล์ `config.yaml` ตามความต้องการ:

```yaml
llm:
  provider: "openai"  # หรือ "llama", "custom"
  model_name: "gpt-3.5-turbo"
  api_key: "your-api-key"
```

## 📖 การใช้งาน

### เริ่มต้นโปรแกรม

```bash
python main.py
```

### โหมดการใช้งาน

#### 1. โหมดข้อความ (Text Mode)
- พิมพ์คำถามและกด Enter
- ระบบจะตอบกลับเป็นข้อความ

#### 2. โหมดเสียง (Voice Mode)
- กล่าว `/mode voice` เพื่อเปลี่ยนโหมด
- พูดคำถามเข้าไมโครโฟน
- ระบบจะตอบกลับด้วยเสียง

### คำสั่งพิเศษ

- `/help` - แสดงความช่วยเหลือ
- `/mode text` - เปลี่ยนเป็นโหมดข้อความ
- `/mode voice` - เปลี่ยนเป็นโหมดเสียง
- `/clear` - ล้างหน้าจอ
- `/stats` - แสดงสถิติระบบ
- `/reload` - โหลดเอกสารใหม่
- `exit` หรือ `quit` - ออกจากโปรแกรม

## 🔧 การตั้งค่า LLM

### 1. ใช้งานกับ OpenAI

```yaml
llm:
  provider: "openai"
  model_name: "gpt-3.5-turbo"
  api_key: "your-openai-api-key"
```

### 2. ใช้งานกับ Llama (Local)

```bash
# ดาวน์โหลด model
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf -O models/llama-2-7b-chat.gguf
```

```yaml
llm:
  provider: "llama"
  llama_model_path: "./models/llama-2-7b-chat.gguf"
```

### 3. ใช้งานกับ Ollama

```bash
# ติดตั้ง Ollama
curl -fsSL https://ollama.com/install.sh | sh

# รัน model
ollama run llama2
```

```yaml
llm:
  provider: "custom"
  base_url: "http://localhost:11434/v1"
  model_name: "llama2"
  api_key: "ollama"  # ใส่อะไรก็ได้
```

## 📚 การเพิ่มเอกสาร

1. วางเอกสารใน folder `data/documents/`
2. รองรับไฟล์: `.txt`, `.pdf`, `.docx`, `.md`
3. เมื่อรันโปรแกรม เลือก "y" เพื่อโหลดเอกสาร
4. หรือใช้คำสั่ง `/reload` เพื่อโหลดเอกสารใหม่

## 🎤 การใช้งานเสียง

### ความต้องการ

- **ไมโครโฟน** สำหรับรับเสียง
- **ลำโพง/หูฟัง** สำหรับเล่นเสียง

### ติดตั้ง Audio Dependencies

#### Windows
```bash
pip install pyaudio
```

#### Linux
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

#### macOS
```bash
brew install portaudio
pip install pyaudio
```

## 🐛 การแก้ไขปัญหา

### 1. ปัญหา PyAudio

```bash
# ถ้าติดตั้ง pyaudio ไม่ได้
pip install pipwin
pipwin install pyaudio
```

### 2. ปัญหา Microphone

```python
# ทดสอบไมโครโฟน
python -c "from src.audio.speech_to_text import SpeechToText; stt = SpeechToText({'engine': 'google'}); stt.test_microphone()"
```

### 3. ปัญหา Memory (สำหรับ Local LLM)

- ลดขนาด model (ใช้ quantized version)
- ลด `max_tokens` ใน config
- ปิดโปรแกรมอื่นๆ

## 📝 ตัวอย่างการใช้งาน

### ตัวอย่าง 1: ถามคำถามทั่วไป

```
👤 คุณ: สวัสดีครับ
🤖 Assistant: สวัสดีครับ! ยินดีให้บริการ มีอะไรให้ช่วยไหมครับ?
```

### ตัวอย่าง 2: ค้นหาจากเอกสาร

```
👤 คุณ: มีข้อมูลอะไรบ้างในเอกสาร
🤖 Assistant: [ค้นหาจากเอกสารและตอบ]
  📚 ใช้ข้อมูลจาก RAG
  📄 แหล่งที่มา: document1.pdf, document2.txt
```

## 🤝 Contributing

Pull requests are welcome! สำหรับการเปลี่ยนแปลงครั้งใหญ่ กรุณาเปิด issue ก่อน

## 📄 License

MIT License

## 👥 Author

[Your Name]

## 🙏 Acknowledgments

- LangChain & LangGraph
- OpenAI
- Anthropic (Claude)
- Whisper (OpenAI)
- ChromaDB

---

**หมายเหตุ:** โปรเจคนี้อยู่ระหว่างการพัฒนา อาจมีการเปลี่ยนแปลงในอนาคต

pip install loguru && pip freeze > requirements.txt
