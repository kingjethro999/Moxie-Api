from moxie import Moxie, JSONResponse, HTTPException
from pydantic import BaseModel

app = Moxie(
    title="Moxie Demo API",
    description="A demonstration of Moxie's **Auto OpenAPI** and **Guards** features.",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

@app.get("/", tags=["General"])
async def index() -> dict:
    """
    Root endpoint.
    
    Returns a simple JSON object indicating the framework is running.
    """
    return {"framework": "Moxie", "status": "running"}

@app.get("/items/{item_id:int}", tags=["Items"])
async def read_item(item_id: int, q: str = None) -> dict:
    """
    Fetch an item by ID.
    
    Args:
        item_id: The unique identifier for the item.
        q: An optional search query.
        
    Raises:
        HTTPException(404): Item not found.
    """
    if item_id > 100:
        raise HTTPException(404, detail="Item not found")
    return {"item_id": item_id, "q": q}

@app.post("/items", tags=["Items"], summary="Create a new item")
async def create_item(item: Item) -> Item:
    """
    Create an item with the provided data.
    
    Returns the created item.
    """
    return item

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
