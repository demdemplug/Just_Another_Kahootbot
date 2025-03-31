from .bases import Event
from pydantic import BaseModel

class Ext(BaseModel):
    timetrack: int

class Data(BaseModel):
    type: str
    cid: str

class ServiceControllerEvent(Event):
    channel: str = "/service/controller"
    ext: Ext
    data: Data

    async def handle(self, instance):
        pass

