"""
BERT Model Server
Fast API server for BERT embeddings and inference
"""

import logging
from typing import List, Dict, Optional
import asyncio
from pathlib import Path

import torch
from transformers import (
    AutoTokenizer,
    AutoModel,
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
    pipeline
)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = "deepset/gbert-large"  # German BERT
NER_MODEL = "deepset/gbert-large-ner-legal"  # German Legal NER
CLASSIFICATION_MODEL = "deepset/gbert-large-classification"
MAX_LENGTH = 512
BATCH_SIZE = 8
USE_GPU = torch.cuda.is_available()

app = FastAPI(title="BERT Model Server", version="1.0.0")

# Global models
tokenizer = None
embedding_model = None
ner_pipeline = None
classification_pipeline = None


class EmbeddingRequest(BaseModel):
    texts: List[str] = Field(..., description="Texts to embed")
    normalize: bool = Field(True, description="Normalize embeddings")
    pooling: str = Field("mean", description="Pooling strategy (mean, max, cls)")


class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimensions: int


class NERRequest(BaseModel):
    text: str = Field(..., description="Text for NER")
    threshold: float = Field(0.5, description="Confidence threshold")


class NERResponse(BaseModel):
    entities: List[Dict]
    model: str


class ClassificationRequest(BaseModel):
    text: str = Field(..., description="Text to classify")
    top_k: int = Field(3, description="Return top K classes")


class ClassificationResponse(BaseModel):
    predictions: List[Dict]
    model: str


@app.on_event("startup")
async def load_models():
    """Load models on startup"""
    global tokenizer, embedding_model, ner_pipeline, classification_pipeline
    
    logger.info("Loading models...")
    
    device = 0 if USE_GPU else -1
    logger.info(f"Using device: {'GPU' if USE_GPU else 'CPU'}")
    
    try:
        # Load tokenizer
        logger.info(f"Loading tokenizer: {MODEL_NAME}")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        
        # Load embedding model
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        embedding_model = AutoModel.from_pretrained(MODEL_NAME)
        
        if USE_GPU:
            embedding_model = embedding_model.cuda()
        
        embedding_model.eval()
        
        # Load NER pipeline
        logger.info(f"Loading NER model: {NER_MODEL}")
        try:
            ner_pipeline = pipeline(
                "ner",
                model=NER_MODEL,
                tokenizer=NER_MODEL,
                device=device,
                aggregation_strategy="simple"
            )
        except Exception as e:
            logger.warning(f"Failed to load NER model: {e}. Using base model.")
            ner_pipeline = pipeline(
                "ner",
                model=MODEL_NAME,
                tokenizer=MODEL_NAME,
                device=device,
                aggregation_strategy="simple"
            )
        
        # Load classification pipeline
        logger.info(f"Loading classification model: {CLASSIFICATION_MODEL}")
        try:
            classification_pipeline = pipeline(
                "text-classification",
                model=CLASSIFICATION_MODEL,
                tokenizer=CLASSIFICATION_MODEL,
                device=device,
                top_k=None
            )
        except Exception as e:
            logger.warning(f"Failed to load classification model: {e}")
            classification_pipeline = None
        
        logger.info("✓ All models loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load models: {e}", exc_info=True)
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "device": "GPU" if USE_GPU else "CPU",
        "models_loaded": {
            "embedding": embedding_model is not None,
            "ner": ner_pipeline is not None,
            "classification": classification_pipeline is not None
        }
    }


@app.post("/embed", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    """
    Create embeddings for texts
    
    Returns dense vector representations suitable for:
    - Semantic similarity
    - Document clustering
    - Neural search
    """
    
    if not embedding_model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        embeddings = []
        
        # Process in batches
        for i in range(0, len(request.texts), BATCH_SIZE):
            batch = request.texts[i:i + BATCH_SIZE]
            
            # Tokenize
            inputs = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors="pt"
            )
            
            if USE_GPU:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Get embeddings
            with torch.no_grad():
                outputs = embedding_model(**inputs)
                
                # Apply pooling strategy
                if request.pooling == "cls":
                    # Use CLS token
                    batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                
                elif request.pooling == "max":
                    # Max pooling
                    batch_embeddings = torch.max(
                        outputs.last_hidden_state,
                        dim=1
                    )[0].cpu().numpy()
                
                else:  # mean (default)
                    # Mean pooling with attention mask
                    attention_mask = inputs["attention_mask"]
                    
                    mask_expanded = attention_mask.unsqueeze(-1).expand(
                        outputs.last_hidden_state.size()
                    ).float()
                    
                    sum_embeddings = torch.sum(
                        outputs.last_hidden_state * mask_expanded,
                        dim=1
                    )
                    sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                    
                    batch_embeddings = (sum_embeddings / sum_mask).cpu().numpy()
            
            # Normalize if requested
            if request.normalize:
                norms = np.linalg.norm(batch_embeddings, axis=1, keepdims=True)
                batch_embeddings = batch_embeddings / norms
            
            embeddings.extend(batch_embeddings.tolist())
        
        return EmbeddingResponse(
            embeddings=embeddings,
            model=MODEL_NAME,
            dimensions=len(embeddings[0])
        )
        
    except Exception as e:
        logger.error(f"Embedding error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ner", response_model=NERResponse)
async def extract_entities(request: NERRequest):
    """
    Extract named entities from text
    
    Recognizes:
    - PER (Person)
    - ORG (Organization)
    - LOC (Location)
    - MISC (Miscellaneous)
    - Legal-specific entities (if legal model loaded)
    """
    
    if not ner_pipeline:
        raise HTTPException(status_code=503, detail="NER model not loaded")
    
    try:
        # Extract entities
        entities = ner_pipeline(request.text)
        
        # Filter by threshold
        filtered_entities = [
            {
                "entity": ent["entity_group"],
                "text": ent["word"],
                "score": float(ent["score"]),
                "start": ent["start"],
                "end": ent["end"]
            }
            for ent in entities
            if ent["score"] >= request.threshold
        ]
        
        return NERResponse(
            entities=filtered_entities,
            model=NER_MODEL
        )
        
    except Exception as e:
        logger.error(f"NER error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest):
    """
    Classify text into categories
    
    Returns top K predictions with confidence scores
    """
    
    if not classification_pipeline:
        raise HTTPException(
            status_code=503,
            detail="Classification model not available"
        )
    
    try:
        # Classify
        results = classification_pipeline(
            request.text,
            top_k=request.top_k
        )
        
        predictions = [
            {
                "label": pred["label"],
                "score": float(pred["score"])
            }
            for pred in results
        ]
        
        return ClassificationResponse(
            predictions=predictions,
            model=CLASSIFICATION_MODEL
        )
        
    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/similarity")
async def compute_similarity(text1: str, text2: str):
    """
    Compute semantic similarity between two texts
    
    Returns cosine similarity score (0-1)
    """
    
    try:
        # Get embeddings
        response = await create_embeddings(
            EmbeddingRequest(
                texts=[text1, text2],
                normalize=True,
                pooling="mean"
            )
        )
        
        # Compute cosine similarity
        emb1 = np.array(response.embeddings[0])
        emb2 = np.array(response.embeddings[1])
        
        similarity = float(np.dot(emb1, emb2))
        
        return {
            "similarity": similarity,
            "text1_preview": text1[:100],
            "text2_preview": text2[:100]
        }
        
    except Exception as e:
        logger.error(f"Similarity error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)