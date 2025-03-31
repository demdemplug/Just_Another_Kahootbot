from pydantic import BaseModel
from .bases import Event  

class Ext(BaseModel):
    ack: int

class Advice(BaseModel):
    interval: int
    timeout: int
    reconnect: str

class MetaConnectEvent(Event):
    channel: str = "/meta/connect"
    ext: Ext
    advice: Advice
    id: str
    successful: bool

    async def handle(self, instance):
        pass
