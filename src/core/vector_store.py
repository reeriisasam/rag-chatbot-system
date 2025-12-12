from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from loguru import logger

class VectorStoreManager:
    """จัดการ Vector Store สำหรับ RAG"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.store_type = config.get('type', 'chroma')
        self.persist_directory = Path(config.get('persist_directory', './data/vector_db'))
        self.embeddings = self._initialize_embeddings()
        self.vector_store = None
        
        # สร้าง directory ถ้ายังไม่มี
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # โหลด vector store ถ้ามีอยู่แล้ว
        self._load_or_create_store()
    
    def _initialize_embeddings(self):
        """สร้าง embeddings model"""
        embeddings_config = self.config.get('embeddings', {})
        model_name = embeddings_config.get('model', 'sentence-transformers/all-MiniLM-L6-v2')
        device = embeddings_config.get('device', 'cpu')
        
        logger.info(f"Initializing embeddings model: {model_name}")
        
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def _load_or_create_store(self):
        """โหลดหรือสร้าง vector store ใหม่"""
        try:
            if self.store_type == 'chroma':
                self.vector_store = self._load_chroma()
            elif self.store_type == 'faiss':
                self.vector_store = self._load_faiss()
            else:
                logger.warning(f"Unknown store type: {self.store_type}, using Chroma")
                self.vector_store = self._load_chroma()
        except Exception as e:
            logger.warning(f"Could not load existing store: {e}. Creating new one.")
            self.vector_store = None
    
    def _load_chroma(self):
        """โหลด Chroma vector store"""
        try:
            return Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embeddings
            )
        except:
            return None
    
    def _load_faiss(self):
        """โหลด FAISS vector store"""
        index_path = self.persist_directory / "index.faiss"
        if index_path.exists():
            return FAISS.load_local(
                str(self.persist_directory),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        return None
    
    def add_documents(self, documents: List[Document]) -> bool:
        """
        เพิ่มเอกสารเข้า vector store
        
        Args:
            documents: รายการของ Document objects
        
        Returns:
            True ถ้าสำเร็จ, False ถ้าล้มเหลว
        """
        try:
            if not documents:
                logger.warning("No documents to add")
                return False
            
            logger.info(f"Adding {len(documents)} documents to vector store")
            
            if self.vector_store is None:
                # สร้าง vector store ใหม่
                if self.store_type == 'chroma':
                    self.vector_store = Chroma.from_documents(
                        documents=documents,
                        embedding=self.embeddings,
                        persist_directory=str(self.persist_directory)
                    )
                else:  # FAISS
                    self.vector_store = FAISS.from_documents(
                        documents=documents,
                        embedding=self.embeddings
                    )
            else:
                # เพิ่มเข้า store ที่มีอยู่
                self.vector_store.add_documents(documents)
            
            # บันทึก
            self.save()
            logger.info("Documents added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Document]:
        """
        ค้นหาเอกสารที่คล้ายกับ query
        
        Args:
            query: คำค้นหา
            k: จำนวนผลลัพธ์ที่ต้องการ
            score_threshold: คะแนนความคล้ายขั้นต่ำ (optional)
        
        Returns:
            รายการของ Document ที่เกี่ยวข้อง
        """
        if self.vector_store is None:
            logger.warning("Vector store is empty")
            return []
        
        try:
            if score_threshold:
                results = self.vector_store.similarity_search_with_score(
                    query, k=k
                )
                # กรอง documents ที่มี score สูงกว่า threshold
                return [doc for doc, score in results if score >= score_threshold]
            else:
                return self.vector_store.similarity_search(query, k=k)
                
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5
    ) -> List[tuple[Document, float]]:
        """ค้นหาพร้อมคะแนนความคล้าย"""
        if self.vector_store is None:
            return []
        
        try:
            return self.vector_store.similarity_search_with_score(query, k=k)
        except Exception as e:
            logger.error(f"Error in similarity search with score: {e}")
            return []
    
    def save(self):
        """บันทึก vector store"""
        try:
            if self.vector_store is None:
                return
            
            if self.store_type == 'chroma':
                # Chroma บันทึกอัตโนมัติ
                if hasattr(self.vector_store, 'persist'):
                    self.vector_store.persist()
            elif self.store_type == 'faiss':
                self.vector_store.save_local(str(self.persist_directory))
            
            logger.info("Vector store saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
    
    def delete_collection(self):
        """ลบ vector store ทั้งหมด"""
        try:
            if self.store_type == 'chroma' and self.vector_store:
                self.vector_store.delete_collection()
            
            # ลบไฟล์
            if self.persist_directory.exists():
                import shutil
                shutil.rmtree(self.persist_directory)
                self.persist_directory.mkdir(parents=True, exist_ok=True)
            
            self.vector_store = None
            logger.info("Vector store deleted")
            
        except Exception as e:
            logger.error(f"Error deleting vector store: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """ดึงสถิติของ vector store"""
        if self.vector_store is None:
            return {'status': 'empty', 'count': 0}
        
        try:
            if self.store_type == 'chroma':
                collection = self.vector_store._collection
                count = collection.count() if hasattr(collection, 'count') else 0
            else:
                count = self.vector_store.index.ntotal if hasattr(self.vector_store, 'index') else 0
            
            return {
                'status': 'active',
                'type': self.store_type,
                'count': count,
                'persist_directory': str(self.persist_directory)
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'status': 'error', 'message': str(e)}