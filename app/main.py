import uvicorn
from fastapi import FastAPI

app = FastAPI()

# Tus rutas aquí...

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)