# app.py

# TODO: importer FastAPI
from fastapi import FastAPI

# TODO: créer une instance FastAPI
appi = FastAPI()

# TODO: définir une route GET /health
@appi.get("/health")
def health():
    return {"status": "ok"}

