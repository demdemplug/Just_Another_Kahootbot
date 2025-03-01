import hypercorn.asyncio
import asyncio
from hypercorn.config import Config
from quart import Quart
from ..api import * 

def run():
    config = Config.from_mapping(bind=["0.0.0.0:8000"])
    asyncio.run(hypercorn.asyncio.serve(app, config)) 