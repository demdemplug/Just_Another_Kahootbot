
import asyncio


class Handler:
    async def handle(self, task: asyncio.Task, swarm):
        raise NotImplementedError(f"handle is not implemented for {self.__class__.__name__}!")
    

class KickedFromGameError(Exception, Handler):
    """Thrown when the host of the kahoot game kicks out the bot"""

    # TODO remove entry in swarm.instancetotask
    async def handle(self, task: asyncio.Task, swarm):
        # simply restart the bot 
        task.cancel()
        # try: 
        #     await task
        # except asyncio.CancelledError:
        #     pass
        swarm.tasks.remove(task)

        swarm.startNewBot()

class SessionNotFoundError(Exception, Handler):

    # nothing else we can do: shut down swarm
    async def handle(self, task: asyncio.Task, swarm):
        swarm.stop = True

class GameEndedError(Exception, Handler):

    async def handle(self, task, swarm):
        swarm.stop = True