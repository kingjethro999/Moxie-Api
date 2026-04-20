from moxie import Moxie

app = Moxie(title="My Awesome API")

@app.get("/")
async def root():
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Welcome to Moxie!"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    """
    Retrieve an item by its ID.
    
    Args:
        item_id: The ID of the item to retrieve.
        q: An optional search query.
    """
    return {"item_id": item_id, "q": q}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
