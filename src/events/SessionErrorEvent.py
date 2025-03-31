from pydantic import BaseModel
from .bases import Event, Ext
from ..Kahoot_Bot.exceptions import SessionNotFoundError
from ..logger import logger

class Data(BaseModel):
    description: str
    type: str
    error: str

class SessionErrorEvent(Event):
    ext: Ext
    data: Data
    channel: str = "/service/controller"

    async def handle(self, instance):
        if self.data.type == "loginResponse" and self.data.error == "NONEXISTING_SESSION":
            raise SessionNotFoundError(f"Game not found: type {self.data.type}, error {self.data.error}")
        logger.error(f"Unknown values. type: {self.data.type}, error: {self.data.error} in {type(SessionErrorEvent)}")
        

