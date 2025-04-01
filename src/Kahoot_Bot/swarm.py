import asyncio
from time import time
from typing import List
from .kahootbot2 import KahootBot
import secrets
from ..logger import logger
from .exceptions import FatalError, SwarmHandler


class Swarm:
    def __init__(self):
        """Initialize the swarm object."""
        self.ttl = None
        self.start_time = time()
        self.tasks: List[asyncio.Task] = []
        self.gameid: int
        self.nickname: str
        self.crash: bool
        self.queue = asyncio.Queue(maxsize=100)  # Errors will be put in here
        self.instancetotask: dict[KahootBot, asyncio.Task] = {}
        self.stop = False
        self.clean_execution: FatalError = None

    def isAlive(self) -> bool:
        """Check if the swarm is still alive based on TTL."""
        return (time() - self.start_time) < self.ttl

    def getTimeRemaining(self) -> int:
        """Calculate the time remaining before TTL expires."""
        return self.ttl - (time() - self.start_time)

    def startNewBot(self):
        """Start a new bot instance and create its task."""
        # if the instance is one simply name the bot without the hash
        if self.amount == 1: 
            instance = KahootBot(self.gameid, self.nickname, self.crash, self.queue)
        else: 
            instance = KahootBot(self.gameid, f"{self.nickname}{secrets.token_hex(4)}", self.crash, self.queue)
        
        task = instance.start()
        self.instancetotask[instance] = task
        self.tasks.append(task)


    def killSwarm(self, error: SwarmHandler):
        """ends the swarm"""
        if isinstance(error, FatalError):
            self.clean_execution = error
        else: 
            logger.error("only allowed to kill Swarm with FatalError")
        self.stop = True


    async def stopBot(self, instance: KahootBot, task: asyncio.Task):
        """stops a bot"""

        task.cancel()

        await task

        self.tasks.remove(task)

        del self.instancetotask[instance]






    # Async functions below

    async def cleanUp(self):
        """Cancel all running tasks."""

        for task in self.tasks:
            
            task.cancel()
            await task  # Ensure graceful cancellation

        
        self.watchdog.cancel()    
        await self.watchdog 
        
       
        self.tasks.clear()
        self.instancetotask.clear()

    

    async def watchDog(self):
        """Listen for errors and handle them when they occur."""
        try:
            while True:
                instance, error = await self.queue.get() # we know that error implements handle that is checked in the bot before sending it over.
                await error.handle(instance, self.instancetotask[instance], self)
                self.queue.task_done()

        except asyncio.CancelledError:
            return

    async def start(self, gameid: int, nickname: str, crash: bool, amount: int, ttl: int):
        """Start the swarm in an async event loop with TTL check."""
        self.gameid = gameid
        self.nickname = nickname
        self.crash = crash
        self.amount = amount
        logger.debug(f"starting {amount} kahoot bot(s) ...")

        self.watchdog = asyncio.create_task(self.watchDog())

        
        for _ in range(int(amount)):
            self.startNewBot()

        # set ttl after bots have started to 
        # make sure bots init dont take up lifetime
        self.ttl = ttl

        # Main loop to check if the swarm is still alive
        while self.isAlive() and not self.stop:
            logger.debug("time remaining: " + str(self.getTimeRemaining()))
            await asyncio.sleep(5)

        await self.cleanUp()

        if not self.clean_execution:
            e = "successfully"
        else:
            e = f"with a error {type(self.clean_execution)}"
        logger.info(f"Swarm with {amount} bot(s) and a lifetime of {ttl} second(s) closed {e}")

    # Task starter for the /swarm endpoint wrapped in a new task as we dont want the endpoint to live for the entire duration of the swarm.
    def createSwarm(self, gameid: int, nickname: str, crash: bool, amount: int, ttl: int):
        """Create a new swarm task and run it asynchronously."""
        logger.info(f"New swarm creation started. Amount: {amount}, TTL: {ttl}, nickname: {nickname}")
        asyncio.create_task(self.start(gameid, nickname, crash, amount, ttl))
