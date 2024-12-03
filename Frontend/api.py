"""API methods to handle products."""
import json
import os
from fastapi import APIRouter, Request, HTTPException
import httpx
from pydantic import BaseModel

BASE_URL = os.getenv("PRODUCTS_BASE_URL", "http://127.0.0.1:8001/products")


class Product(BaseModel):
    name: str
    description: str
    price: float
    in_stock: bool


product_router = APIRouter(prefix="/products", tags=["products"])


@product_router.get("")
async def list_product():
    """Get a list of all the products."""
    async with httpx.AsyncClient() as client:
        res = await client.get(BASE_URL)
        if res.status_code == 200:
            return res.json()
        raise HTTPException(status_code=res.status_code, detail=res.text)


@product_router.post("")
async def add_product(req: Request):
    """Add a new product."""
    try:
        data = Product(**await req.json())
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid product data")
    async with httpx.AsyncClient() as client:
        res = await client.post(BASE_URL, json=data.dict())
        if res.status_code == 200:
            return res.json()
        raise HTTPException(status_code=res.status_code, detail=res.text)


@product_router.get("/{spec_id}")
async def get_product(spec_id: str):
    """Get the product associated with spec_id."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/{spec_id}")
        if res.status_code == 200:
            return res.json()
        raise HTTPException(status_code=res.status_code, detail=res.text)


@product_router.put("/{spec_id}")
async def update_product(spec_id: str, req: Request):
    """Update the product associated with spec_id."""
    data = await req.json()
    async with httpx.AsyncClient() as client:
        res = await client.put(f"{BASE_URL}/{spec_id}", json=data)
        if res.status_code == 200:
            return res.json()
        raise HTTPException(status_code=res.status_code, detail=res.text)


@product_router.delete("/{spec_id}")
async def delete_product(spec_id: str):
    """Delete the product associated with spec_id."""
    async with httpx.AsyncClient() as client:
        res = await client.delete(f"{BASE_URL}/{spec_id}")
        if res.status_code == 200:
            return res.json()
        raise HTTPException(status_code=res.status_code, detail=res.text)
