from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from loguru import logger

class ChatState(TypedDict):
    """State สำหรับ Chat workflow"""
    messages: List[BaseMessage]
    query: str
    context: str
    response: str
    use_rag: bool
    mode: str  # 'text' or 'voice'

class RAGChatWorkflow:
    """LangGraph workflow สำหรับ RAG Chatbot"""
    
    def __init__(self, llm_manager, retriever):
        self.llm = llm_manager
        self.retriever = retriever
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """สร้าง LangGraph workflow"""
        
        # สร้าง StateGraph
        workflow = StateGraph(ChatState)
        
        # เพิ่ม nodes
        workflow.add_node("classify", self._classify_query)
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("generate", self._generate_response)
        workflow.add_node("direct_response", self._direct_response)
        
        # กำหนด entry point
        workflow.set_entry_point("classify")
        
        # เพิ่ม conditional edges
        workflow.add_conditional_edges(
            "classify",
            self._should_use_rag,
            {
                "retrieve": "retrieve",
                "direct": "direct_response"
            }
        )
        
        # เพิ่ม edges
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        workflow.add_edge("direct_response", END)
        
        return workflow.compile()
    
    def _classify_query(self, state: ChatState) -> ChatState:
        """
        จำแนกว่าควรใช้ RAG หรือไม่
        """
        query = state['query']
        
        # คำที่บ่งบอกว่าควรใช้ RAG
        rag_keywords = [
            'เอกสาร', 'ไฟล์', 'ข้อมูล', 'บทความ',
            'หาข้อมูล', 'ค้นหา', 'มีอะไรบ้าง',
            'จากไฟล์', 'ในเอกสาร'
        ]
        
        # เช็คว่ามี keyword ที่ต้องใช้ RAG หรือไม่
        use_rag = any(keyword in query.lower() for keyword in rag_keywords)
        
        # เพิ่ม logic เพิ่มเติมได้ตามต้องการ
        state['use_rag'] = use_rag
        
        logger.info(f"Query classified: use_rag={use_rag}")
        return state
    
    def _should_use_rag(self, state: ChatState) -> str:
        """ตัดสินใจว่าจะไปที่ node ไหน"""
        return "retrieve" if state['use_rag'] else "direct"
    
    def _retrieve_context(self, state: ChatState) -> ChatState:
        """
        ดึง context จาก RAG
        """
        query = state['query']
        logger.info("Retrieving context from RAG")
        
        try:
            context = self.retriever.retrieve_and_format(query)
            state['context'] = context
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            state['context'] = ""
        
        return state
    
    def _generate_response(self, state: ChatState) -> ChatState:
        """
        สร้างคำตอบโดยใช้ LLM พร้อม context
        """
        query = state['query']
        context = state.get('context', '')
        
        logger.info("Generating response with RAG context")
        
        try:
            response = self.llm.generate_with_context(
                query=query,
                context=context
            )
            state['response'] = response
            
            # เพิ่มใน messages
            state['messages'].append(HumanMessage(content=query))
            state['messages'].append(AIMessage(content=response))
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            state['response'] = f"ขออภัย เกิดข้อผิดพลาด: {str(e)}"
        
        return state
    
    def _direct_response(self, state: ChatState) -> ChatState:
        """
        สร้างคำตอบโดยตรงโดยไม่ใช้ RAG
        """
        query = state['query']
        messages = state.get('messages', [])
        
        logger.info("Generating direct response")
        
        try:
            # เพิ่ม query ใหม่เข้าไปใน messages
            messages_copy = messages.copy()
            messages_copy.append(HumanMessage(content=query))
            
            response = self.llm.generate(messages_copy)
            state['response'] = response
            
            # อัพเดท messages
            state['messages'].append(HumanMessage(content=query))
            state['messages'].append(AIMessage(content=response))
            
        except Exception as e:
            logger.error(f"Error generating direct response: {e}")
            state['response'] = f"ขออภัย เกิดข้อผิดพลาด: {str(e)}"
        
        return state
    
    def run(self, query: str, messages: List[BaseMessage] = None, mode: str = "text") -> dict:
        """
        รัน workflow
        
        Args:
            query: คำถามจากผู้ใช้
            messages: ประวัติการสนทนา (optional)
            mode: โหมด ('text' หรือ 'voice')
        
        Returns:
            dict ที่มี 'response' และ 'messages'
        """
        initial_state = ChatState(
            messages=messages or [],
            query=query,
            context="",
            response="",
            use_rag=False,
            mode=mode
        )
        
        try:
            result = self.graph.invoke(initial_state)
            return {
                'response': result['response'],
                'messages': result['messages'],
                'context': result.get('context', ''),
                'use_rag': result.get('use_rag', False)
            }
        except Exception as e:
            logger.error(f"Error running workflow: {e}")
            return {
                'response': f"ขออภัย เกิดข้อผิดพลาด: {str(e)}",
                'messages': messages or [],
                'context': '',
                'use_rag': False
            }
    
    async def arun(self, query: str, messages: List[BaseMessage] = None, mode: str = "text") -> dict:
        """Async version ของ run"""
        # สำหรับ async version สามารถใช้ ainvoke ได้
        initial_state = ChatState(
            messages=messages or [],
            query=query,
            context="",
            response="",
            use_rag=False,
            mode=mode
        )
        
        try:
            result = await self.graph.ainvoke(initial_state)
            return {
                'response': result['response'],
                'messages': result['messages'],
                'context': result.get('context', ''),
                'use_rag': result.get('use_rag', False)
            }
        except Exception as e:
            logger.error(f"Error running workflow: {e}")
            return {
                'response': f"ขออภัย เกิดข้อผิดพลาด: {str(e)}",
                'messages': messages or [],
                'context': '',
                'use_rag': False
            }