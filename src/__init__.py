import hypercorn.asyncio
import asyncio
from hypercorn.config import Config
from quart import Quart
from .api import app 
from .logger import logger

def run():
    config = Config.from_mapping(bind=["0.0.0.0:8000"])
    asyncio.run(hypercorn.asyncio.serve(app, config)) 