from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from random import randint

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/hello")
async def root():
    """
    returns Hello
    """
    return PlainTextResponse("Hello !")


@app.get("/random")
async def random():
    """
    random numb
    """
    for i in range(1, 100000000):
        pass
    return JSONResponse({"random_number": randint(1, 999)})
