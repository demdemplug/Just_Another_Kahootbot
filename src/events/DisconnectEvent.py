from pydantic import BaseModel
from .bases import Event
from ..Kahoot_Bot.exceptions import HostDisconnectError
from ...config.logger import logger

class Ext(BaseModel):
    timetrack: int

class Data(BaseModel):
    reason: str
    type: str
    status: str

class DisconnectEvent(Event):
    ext: Ext
    data: Data
    channel: str = "/service/status"

    async def handle(self, instance):
        if self.data.reason == "disconnect" and self.data.status == "MISSING":
            raise HostDisconnectError("Host disconnect from game.")
        logger.warning(f"unknown value in {type(DisconnectEvent)} disconnect: {self.data.reason}, status: {self.data.status} ")
