from typing import List, Dict, Any
from langchain_core.documents import Document
from loguru import logger

class RAGRetriever:
    """จัดการการดึงข้อมูลที่เกี่ยวข้องสำหรับ RAG"""
    
    def __init__(self, vector_store_manager, config: Dict[str, Any]):
        self.vector_store = vector_store_manager
        self.config = config
        self.top_k = config.get('top_k', 5)
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
    
    def retrieve(self, query: str) -> List[Document]:
        """
        ดึงเอกสารที่เกี่ยวข้องกับ query
        
        Args:
            query: คำถามจากผู้ใช้
        
        Returns:
            รายการของ Document ที่เกี่ยวข้อง
        """
        try:
            logger.info(f"Retrieving documents for query: {query[:50]}...")
            
            results = self.vector_store.similarity_search(
                query=query,
                k=self.top_k,
                score_threshold=self.similarity_threshold
            )
            
            logger.info(f"Retrieved {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def retrieve_with_scores(self, query: str) -> List[tuple[Document, float]]:
        """ดึงเอกสารพร้อมคะแนนความคล้าย"""
        try:
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=self.top_k
            )
            
            # กรองตาม threshold
            filtered = [
                (doc, score) for doc, score in results 
                if score >= self.similarity_threshold
            ]
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error retrieving documents with scores: {e}")
            return []
    
    def format_context(self, documents: List[Document]) -> str:
        """
        จัดรูปแบบ documents เป็น context string
        
        Args:
            documents: รายการของ Document
        
        Returns:
            Context string
        """
        if not documents:
            return "ไม่มีข้อมูลที่เกี่ยวข้อง"
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.page_content
            source = doc.metadata.get('source', 'Unknown')
            
            context_parts.append(
                f"[เอกสาร {i} - {source}]\n{content}"
            )
        
        return "\n\n".join(context_parts)
    
    def retrieve_and_format(self, query: str) -> str:
        """ดึงเอกสารและจัดรูปแบบ context ในคำสั่งเดียว"""
        documents = self.retrieve(query)
        return self.format_context(documents)
    
    def get_relevant_sources(self, query: str) -> List[str]:
        """ดึงรายการแหล่งที่มาของเอกสารที่เกี่ยวข้อง"""
        documents = self.retrieve(query)
        sources = []
        
        for doc in documents:
            source = doc.metadata.get('source', 'Unknown')
            if source not in sources:
                sources.append(source)
        
        return sources