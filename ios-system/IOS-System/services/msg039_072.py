"""
GPT integration for summarization and Q&A
"""

from openai import AsyncOpenAI

class GPTService:
    """GPT-powered features"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def summarize(self, text: str, max_words: int = 100) -> str:
        """Generate document summary"""
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": f"Summarize the following document in {max_words} words or less."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    async def answer_question(
        self,
        question: str,
        context_documents: List[str]
    ) -> Dict:
        """Answer question based on documents"""
        
        context = "\n\n---\n\n".join(context_documents)
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "Answer questions based on the provided documents. "
                              "If the answer is not in the documents, say so."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}"
                }
            ],
            temperature=0.1
        )
        
        return {
            "answer": response.choices[0].message.content,
            "sources": self._extract_sources(response)
        }
    
    async def generate_tags(self, text: str) -> List[str]:
        """Auto-generate relevant tags"""
        
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Generate 5 relevant tags for this document. "
                              "Return as JSON array."
                },
                {
                    "role": "user",
                    "content": text[:2000]  # First 2K chars
                }
            ],
            temperature=0.5
        )
        
        return json.loads(response.choices[0].message.content)