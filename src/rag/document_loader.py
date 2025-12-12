from typing import List, Dict
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader
)
from loguru import logger

class DocumentLoader:
    """โหลดและประมวลผลเอกสารจากไฟล์ต่างๆ"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.chunk_size = config.get('chunk_size', 1000)
        self.chunk_overlap = config.get('chunk_overlap', 200)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        
        # Loader สำหรับแต่ละประเภทไฟล์
        self.loaders = {
            '.txt': TextLoader,
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.md': UnstructuredMarkdownLoader,
        }
    
    def load_file(self, file_path: str) -> List[Document]:
        """
        โหลดไฟล์เดียว
        
        Args:
            file_path: path ของไฟล์
        
        Returns:
            รายการของ Document chunks
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        extension = path.suffix.lower()
        
        if extension not in self.loaders:
            logger.warning(f"Unsupported file type: {extension}")
            return []
        
        try:
            logger.info(f"Loading file: {file_path}")
            
            # เลือก loader ตามประเภทไฟล์
            loader_class = self.loaders[extension]
            loader = loader_class(str(path))
            
            # โหลดเอกสาร
            documents = loader.load()
            
            # แยก chunk
            chunks = self.text_splitter.split_documents(documents)
            
            # เพิ่ม metadata
            for chunk in chunks:
                chunk.metadata['source'] = path.name
                chunk.metadata['file_path'] = str(path)
            
            logger.info(f"Loaded {len(chunks)} chunks from {path.name}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return []
    
    def load_directory(self, directory_path: str) -> List[Document]:
        """
        โหลดไฟล์ทั้งหมดใน directory
        
        Args:
            directory_path: path ของ directory
        
        Returns:
            รายการของ Document chunks ทั้งหมด
        """
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            return []
        
        all_documents = []
        supported_formats = self.config.get(
            'supported_formats',
            ['.txt', '.pdf', '.docx', '.md']
        )
        
        logger.info(f"Loading documents from: {directory_path}")
        
        # ค้นหาไฟล์ทั้งหมด
        for ext in supported_formats:
            files = list(path.glob(f"**/*{ext}"))
            logger.info(f"Found {len(files)} {ext} files")
            
            for file_path in files:
                docs = self.load_file(str(file_path))
                all_documents.extend(docs)
        
        logger.info(f"Total documents loaded: {len(all_documents)}")
        return all_documents
    
    def load_text(self, text: str, source: str = "text_input") -> List[Document]:
        """
        โหลดข้อความโดยตรง
        
        Args:
            text: ข้อความที่ต้องการโหลด
            source: ชื่อแหล่งที่มา
        
        Returns:
            รายการของ Document chunks
        """
        try:
            # สร้าง Document
            doc = Document(
                page_content=text,
                metadata={'source': source}
            )
            
            # แยก chunk
            chunks = self.text_splitter.split_documents([doc])
            
            logger.info(f"Created {len(chunks)} chunks from text input")
            return chunks
            
        except Exception as e:
            logger.error(f"Error loading text: {e}")
            return []
    
    def update_config(self, chunk_size: int = None, chunk_overlap: int = None):
        """อัพเดท configuration"""
        if chunk_size:
            self.chunk_size = chunk_size
            self.config['chunk_size'] = chunk_size
        
        if chunk_overlap:
            self.chunk_overlap = chunk_overlap
            self.config['chunk_overlap'] = chunk_overlap
        
        # สร้าง text splitter ใหม่
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        
        logger.info(f"Updated config: chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}")