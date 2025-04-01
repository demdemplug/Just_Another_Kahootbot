
import asyncio
from ..logger import logger
class SwarmHandler(Exception):
    async def handle(self, instance, task: asyncio.Task, swarm):
        raise NotImplementedError(f"handle is not implemented for {self.__class__.__name__}!")
    



class KickedFromGameError(SwarmHandler):
    """Thrown when the host of the kahoot game kicks out the bot"""

    async def handle(self, instance, task: asyncio.Task, swarm):
        
        # simply restart the bot 
        logger.info("worky")
        await swarm.stopBot(instance, task)

        swarm.startNewBot()

        
class FatalError(SwarmHandler):
    async def handle(self, instance, task: asyncio.Task, swarm):
        # simply restart the bot 
        await swarm.killSwarm(instance, task)

class TooManyPlayersError(FatalError):
    pass
class HostDisconnectError(FatalError):
    pass

class SessionNotFoundError(FatalError):
    pass
class GameEndedError(FatalError):
    pass
