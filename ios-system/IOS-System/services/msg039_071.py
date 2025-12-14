"""
Transformer-based models for classification and search
"""

from transformers import AutoTokenizer, AutoModel
import torch
from typing import List

class TransformerClassifier:
    """BERT-based document classifier"""
    
    def __init__(self, model_name: str = "bert-base-multilingual-cased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.classifier_head = torch.nn.Linear(768, NUM_CLASSES)
    
    async def classify(self, text: str) -> Dict:
        """Classify using BERT"""
        
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0, :]  # CLS token
        
        # Classify
        logits = self.classifier_head(embeddings)
        probabilities = torch.softmax(logits, dim=1)
        
        predicted_class = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0, predicted_class].item()
        
        return {
            "document_type": CLASS_NAMES[predicted_class],
            "confidence": confidence,
            "all_probabilities": probabilities[0].tolist()
        }
    
    def get_embedding(self, text: str) -> List[float]:
        """Get text embedding for neural search"""
        
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            embedding = outputs.last_hidden_state[:, 0, :].squeeze()
        
        return embedding.tolist()