from pydantic import BaseModel
from .bases import Event

class Ext(BaseModel):
    timetrack: int

class StatusData(BaseModel):
    type: str
    status: str

class ServiceStatusEvent(Event):
    ext: Ext
    data: StatusData
    channel: str = "/service/status"


    async def handle(self, instance):
        pass
