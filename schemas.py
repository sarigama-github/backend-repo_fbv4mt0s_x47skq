"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional

# Study app schemas

class Topic(BaseModel):
    """
    Topics collection schema
    Collection name: "topic"
    """
    name: str = Field(..., min_length=1, max_length=100, description="Topic name")
    description: Optional[str] = Field(None, max_length=300, description="Short description")

class Card(BaseModel):
    """
    Flashcards collection schema
    Collection name: "card"
    """
    topic_id: str = Field(..., description="Reference to Topic _id as string")
    question: str = Field(..., min_length=1, max_length=1000, description="Question side")
    answer: str = Field(..., min_length=1, max_length=2000, description="Answer side")
    difficulty: Optional[str] = Field("medium", description="easy | medium | hard")

class StudyLog(BaseModel):
    """
    Study sessions log
    Collection name: "studylog"
    """
    card_id: str = Field(..., description="Reference to Card _id as string")
    topic_id: str = Field(..., description="Reference to Topic _id as string")
    correct: bool = Field(..., description="Whether the user answered correctly")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
