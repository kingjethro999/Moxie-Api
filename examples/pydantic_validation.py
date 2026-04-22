from pydantic import BaseModel, Field

from moxie import Moxie


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    email: str
    age: int = Field(..., gt=0)

app = Moxie(title="Pydantic Validation Trial")

@app.post("/users")
async def create_user(user: UserCreate):
    """
    This handler demonstrates automatic Pydantic validation.
    Moxie will parse the JSON body and validate it against the UserCreate model.
    """
    return {
        "message": "User created successfully",
        "user": user
    }

@app.get("/search")
async def search(q: str, limit: int = 10):
    """
    This handler demonstrates automatic query parameter inference.
    'q' and 'limit' are pulled from the query string.
    """
    return {
        "query": q,
        "limit": limit
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
