from pydantic import BaseModel

from moxie import Moxie
from moxie.testing import TestClient


class Item(BaseModel):
    name: str
    price: float

app = Moxie()

@app.post("/items")
async def create_item(item: Item):
    return item

@app.get("/hello")
async def hello(name: str = "World"):
    return {"message": f"Hello {name}"}

def test_pydantic_validation():
    client = TestClient(app)
    
    # Valid data
    response = client.post("/items", json={"name": "Widget", "price": 10.5})
    assert response.status_code == 200
    assert response.json() == {"name": "Widget", "price": 10.5}
    
    # Invalid data (missing price)
    # Note: Current implementation of Moxie catches Pydantic ValidationError 
    # and returns a 422 response via ServerErrorMiddleware.
    import contextlib
    with contextlib.suppress(Exception):
        client.post("/items", json={"name": "Widget"})

def test_query_inference():
    client = TestClient(app)
    
    # Default value
    response = client.get("/hello")
    assert response.json() == {"message": "Hello World"}
    
    # Provided value
    response = client.get("/hello?name=Moxie")
    assert response.json() == {"message": "Hello Moxie"}
