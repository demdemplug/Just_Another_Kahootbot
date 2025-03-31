from pydantic import BaseModel
from .bases import Event  


class Ext(BaseModel):
    ack: int

class MetaConnectEventV2(Event):
    channel: str = "/meta/connect"
    ext: Ext
    id: str
    successful: bool

    async def handle(self, instance):
        pass


