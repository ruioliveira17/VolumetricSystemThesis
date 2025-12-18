from fastapi import FastAPI, Path, Query, HTTPException, status
from typing import Optional
from pydantic import BaseModel
from CameraOptions import openCamera, closeCamera, statusCamera
from GetFrame import getFrameClass
from MaskState import maskState
import sys

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    brand: Optional[str] = None

class UpdateItem(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None

inventory = {}

#inventory = {
#    1: {
#        "name": "Milk",
#        "price": 3.99,
#        "brand": "Regular"
#    }
#}

#Obter

@app.get("/")
def home():
    return {"Data": "Testing"}

@app.get("/about")
def about():
    return {"Data": "About"}

@app.get("/item/{item_id}")
def item(item_id: int = Path(..., description="The ID of the item you'd like to view")):
    return inventory[item_id]

#@app.get("/item/{item_id}/{name}")
#def item(item_id: int, name: str):
#    return inventory[item_id]

#@app.get("/name")
#def item(*, name: Optional[str] = None, test: int):
#    for item_id in inventory:
#        if inventory[item_id]["name"] == name:
#            return inventory[item_id]
#    return {"Data": "Not found"}

@app.get("/name")
def item(name: str = Query(None, title="Name", description="Name of item", max_length=10, min_length=2)):
    for item_id in inventory:
        if inventory[item_id].name == name:
            return inventory[item_id]
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Item name not found.")

#Criar

@app.post("/create/{item_id}")
def create(item_id: int, item: Item):
    if item_id in inventory:
        return {"Error": "Item ID already exists"}
    
    inventory[item_id] = item
    return inventory[item_id]

#Atualizar

@app.put("/update/{item_id}")
def update(item_id: int, item: UpdateItem):
    if item_id not in inventory:
        return {"Error": "Item ID does not exists"}
    
    if item.name != None:
        inventory[item_id].name = item.name
    if item.price != None:
        inventory[item_id].price = item.price
    if item.brand != None:
        inventory[item_id].brand = item.brand
    return inventory[item_id]

#Apagar

@app.delete("/delete")
def delete(item_id : int = Query(..., description="The ID of the item to delete", gt=0)):
    if item_id not in inventory:
        return {"Error": "Item ID does not exists"}
    
    del inventory[item_id]
    return {"Success": "Item Deleted!"}

#Camera
@app.post("/openCamera")
def open():
    return openCamera()

@app.post("/closeCamera")
def close():
    return closeCamera()

@app.get("/status")
def status():
    return statusCamera()

#Frame

@app.post("/getFrame")
def frame():
    return getFrameClass()

#Mask

@app.get("/mask/hmin")
def gethmin():
    return{"hmin": maskState.hmin}