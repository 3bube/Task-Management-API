from fastapi import FastAPI, HTTPException, status, Depends
import logging
from pymongo.collection import Collection 
from bson import ObjectId
from database import get_database
from typing import List, Dict, Any

from fastapi.responses import JSONResponse
from models import Task, TaskCreate, TaskStatus, TaskUpdate, PyObjectId
from datetime import datetime

import uvicorn

app = FastAPI(
    title="Task Management API",
    description="Learning FastAPI by building a task management application",
    version="0.1.0",
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    yield
    logger.info("Shutting down...")

# Database dependency
def get_task_collection():
    db = get_database()()
    return db.tasks

@app.get("/")
def read_root():
    return {"message": "Task management API is running!"}

@app.post("/tasks/", response_model=Task)
def create_task(task: TaskCreate, collection: Collection = Depends(get_task_collection)):
    new_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        created_at=datetime.utcnow()
    )
    
    result = collection.insert_one(new_task.dict(by_alias=True))
    created_task = collection.find_one({"_id": result.inserted_id})
    
    return Task(**created_task)


@app.get("/tasks/", response_model=List[Task])
def get_tasks(status: TaskStatus = None, limit: int = 10, collection: Collection = Depends(get_task_collection)):
    query = {}
    if status:
        query["status"] = status
        
    cursor = collection.find(query).limit(limit)
    tasks = list(cursor)
    
    return tasks

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str, collection: Collection = Depends(get_task_collection)):
    try:
        # Convert string ID to ObjectId
        task = collection.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return Task(**task)
    except:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, task_update: TaskUpdate, collection: Collection = Depends(get_task_collection)):
    try:
        task_id_obj = ObjectId(task_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
        
    # Build the update document with only non-None fields
    update_data = {k: v for k, v in task_update.dict(exclude_unset=True).items() if v is not None}
    if not update_data:
        # No fields to update
        task = collection.find_one({"_id": task_id_obj})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return Task(**task)
    
    # Update task in database
    result = collection.update_one(
        {"_id": task_id_obj}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Return updated task
    updated_task = collection.find_one({"_id": task_id_obj})
    return Task(**updated_task)

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, collection: Collection = Depends(get_task_collection)):
    try:
        task_id_obj = ObjectId(task_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    # First find the task to get its title for the response message
    task = collection.find_one({"_id": task_id_obj})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    # Delete the task
    collection.delete_one({"_id": task_id_obj})
    return {"message": f"Task '{task['title']}' deleted successfully"}


@app.get("/tasks/stats")
def get_task_stats(collection: Collection = Depends(get_task_collection)):
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "latest_task": {"$max": "$created_at"}
            }
        },
        {
            "$project": {
                "status": "$_id",
                "count": 1,
                "latest_task": 1,
                "_id": 0
            }
        }
    ]
    
    stats = list(collection.aggregate(pipeline))
    total_tasks = collection.count_documents({})
    
    return {
        "total_tasks": total_tasks,
        "status_breakdown": stats,
        "database_info": "MongoDB Atlas - Global clusters!"
    }

@app.get("/tasks/search")
def search_tasks(q: str, collection: Collection = Depends(get_task_collection)):
    # Text search using regex
    regex_pattern = {"$regex": q, "$options": "i"}
    
    tasks = list(collection.find({
        "$or": [
            {"title": regex_pattern},
            {"description": regex_pattern}
        ]
    }))
    
    for task in tasks:
        task["id"] = str(task.pop("_id"))
    
    return {"query": q, "results": tasks, "count": len(tasks)}


@app.exception_handler(ValueError)
def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, access_log=True)