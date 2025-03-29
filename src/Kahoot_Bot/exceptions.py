
import asyncio



class Handler:
    async def handle(self, instance, task: asyncio.Task, swarm):
        raise NotImplementedError(f"handle is not implemented for {self.__class__.__name__}!")
    

class KickedFromGameError(Exception, Handler):
    """Thrown when the host of the kahoot game kicks out the bot"""

    async def handle(self, instance, task: asyncio.Task, swarm):
        
        # simply restart the bot 
        await swarm.stopBot(instance, task)

        swarm.startNewBot()
        swarm.startNewBot()

class SessionNotFoundError(Exception, Handler):

    # nothing else we can do: shut down swarm
    async def handle(self, instance, task: asyncio.Task, swarm):
        swarm.killSwarm()

class GameEndedError(Exception, Handler):

    async def handle(self, task, swarm):
        swarm.killSwarm()

