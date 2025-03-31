from pydantic import BaseModel
from .bases import Event  

class Ext(BaseModel):
    timetrack: int

class ServiceControllerEventV2(Event):
    channel: str = "/service/controller"
    ext: Ext
    id: str
    successful: bool

    async def handle(self, instance):
        pass
