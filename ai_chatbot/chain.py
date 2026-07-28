import os
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from ai_chatbot.retriever import VectorRetriever
from sqlalchemy.orm import Session

class TravelChatChain:
    def __init__(self, db_session: Session):
        self.retriever = VectorRetriever(db_session)
        
        # Load system prompt
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r") as f:
                self.system_prompt = f.read()
        else:
            self.system_prompt = "You are a helpful travel assistant for Golden Star Agency."
            
        # Initialize Anthropic LLM (can switch to Groq based on API configuration)
        api_key = os.getenv("CLAUDE_API_KEY", "")
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            anthropic_api_key=api_key if api_key else "mock-key"
        )
        
        # Build prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt + "\n\nRetrieved Travel Inventory:\n{context}"),
            ("human", "{question}")
        ])
        
    def generate_response(self, question: str) -> str:
        """
        Retrieves context, binds parameters, and queries LLM using LangChain.
        """
        # Retrieve packages
        packages = self.retriever.retrieve_similar_packages(question)
        
        # Format context
        if packages:
            context = "\n".join([
                f"- Name: {p['title']}, Category: {p['category']}, Price: PKR {p['price']}, Details: {p['description']}"
                for p in packages
            ])
        else:
            context = "No direct matching packages found in inventory."
            
        # Build simple chain
        chain = (
            self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        try:
            response = chain.invoke({"context": context, "question": question})
            return response
        except Exception as e:
            # Fallback mock answer if API key is not active
            return f"Assalamu Alaikum! (AI Mock Mode) Regarding '{question}', please consult one of our packages or check back once keys are active. Error: {e}"
