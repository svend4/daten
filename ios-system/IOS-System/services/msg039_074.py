"""
Real-time collaborative editing with Operational Transformation
"""

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Operation:
    """Text operation for OT"""
    type: str  # 'insert', 'delete', 'retain'
    position: int
    text: Optional[str] = None
    length: Optional[int] = None
    user_id: str = ""
    timestamp: float = 0

class CollaborativeEditor:
    """Collaborative editing engine"""
    
    def __init__(self):
        self.documents = {}  # doc_id -> DocumentState
        self.connections = {}  # doc_id -> List[WebSocket]
    
    async def apply_operation(
        self,
        doc_id: str,
        operation: Operation,
        user_id: str
    ) -> Operation:
        """Apply operation with OT"""
        
        doc_state = self.documents[doc_id]
        
        # Transform against concurrent operations
        transformed_op = self._transform(
            operation,
            doc_state.pending_operations
        )
        
        # Apply to document
        doc_state.apply(transformed_op)
        
        # Broadcast to other users
        await self._broadcast_operation(
            doc_id,
            transformed_op,
            exclude_user=user_id
        )
        
        # Create version snapshot
        if doc_state.should_snapshot():
            await self._create_snapshot(doc_id)
        
        return transformed_op
    
    def _transform(
        self,
        op1: Operation,
        concurrent_ops: List[Operation]
    ) -> Operation:
        """Operational Transformation"""
        
        transformed = op1
        
        for op2 in concurrent_ops:
            if op1.type == "insert" and op2.type == "insert":
                if op2.position < op1.position:
                    transformed.position += len(op2.text)
                    
            elif op1.type == "delete" and op2.type == "insert":
                if op2.position <= op1.position:
                    transformed.position += len(op2.text)
            
            # More transformation rules...
        
        return transformed