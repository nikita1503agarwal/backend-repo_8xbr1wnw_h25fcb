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
from typing import Optional, List, Literal

# Example schemas (you can keep or ignore in your app)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# DASS-21 assessment schema
class DASSAssessment(BaseModel):
    """Collection: "dassassessment". Stores a completed DASS-21 assessment.
    Answers must be a list of 21 integers (0-3).
    """
    student_name: Optional[str] = Field(None, description="Student full name")
    student_email: Optional[str] = Field(None, description="Student email")
    age: Optional[int] = Field(None, ge=5, le=120)
    context: Optional[str] = Field(None, description="Class, course, or notes")
    answers: List[int] = Field(..., min_items=21, max_items=21, description="21 responses scored 0-3")

class DASSResult(BaseModel):
    depression_score: int
    anxiety_score: int
    stress_score: int
    depression_severity: Literal['Normal','Mild','Moderate','Severe','Extremely Severe']
    anxiety_severity: Literal['Normal','Mild','Moderate','Severe','Extremely Severe']
    stress_severity: Literal['Normal','Mild','Moderate','Severe','Extremely Severe']
    total_score: int
    assessment_id: Optional[str] = None
