from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional
from bson import ObjectId

# PyObjectId for proper handling of MongoDB ObjectIds
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
        
    @classmethod
    def __get_pydantic_json_schema__(cls, schema_generator):
        return schema_generator.get_schema_for_type(str)

class TaskStatus(str, Enum):
    pending      = "pending"
    in_progress  = "in_progress"
    completed    = "completed"

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 1

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[TaskStatus] = None

    class Config:
        extra = "forbid"

class Task(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.pending
    priority: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }