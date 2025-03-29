import requests
import asyncio
import websockets
import random
import uuid
import json
import time
from .payloads import Payloads
from .exceptions import *
from ..challenge.runchallenge import runChallenge
import traceback
from ..logger import logger







class KahootBot:

    def __init__(self, gameid: int, nickname: str, crash: bool, queue: asyncio.Queue):
        self.gameid = gameid
        self.nickname = nickname
        self.crash = crash
        self.ack = 2
        self.id = 6
        self.wsocket = None
        self.errorHandler = queue
        self.sendHartebeat = True
        self.childTasks = []

    def start(self):
        return asyncio.create_task(self.watchDog())

    async def watchDog(self):
        try: 
            await self.connect()
            while True:
                for task in self.childTasks:
                    if task.done():
                        if isinstance(task.exception(), Handler):
                            await self.errorHandler.put((self, task.exception()))
                            logger.error(f"watchDog: {task.exception()} type: {type(task.exception())}")
                            return
                        logger.error(f"watchDog found an unhandled error: {task.exception()}")
                        return
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Unhandled error: {e}")
            traceback.format_exc()
        finally:
            await self.cleanUp()

    async def connect(self):
        """Handles connecting to the Kahoot WebSocket server."""
        cookies = {
            "generated_uuid": str(uuid.uuid4()),
            "player": "active"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"
        }

        try:
            response = requests.get(
                f'https://kahoot.it/reserve/session/{self.gameid}/?{time.time()}',
                headers=headers,
                cookies=cookies
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch challenge: {e}")
            return

        try:
            challenge_response = runChallenge(response.json()['challenge'], response.headers['x-kahoot-session-token'])
        except Exception as e:
            logger.error(f"Challenge function failed: {e}")
            return

        logger.info(f"WebSocket URL: wss://kahoot.it/cometd/{self.gameid}/{challenge_response}")

        logger.info(f"Connecting to WebSocket...")
    
        self.wsocket = await websockets.connect(
            f'wss://kahoot.it/cometd/{self.gameid}/{challenge_response}',
            ping_interval=30, 
            ping_timeout=60,
            open_timeout=30
        )
        logger.info(f"Connected!")
        await self.initialize_connection()
        self.childTasks.append(asyncio.create_task(self.heartBeat()))
        self.childTasks.append(asyncio.create_task(self.receiveMessages()))
            
        if self.crash:
            self.childTasks.append(asyncio.create_task(self.crasher()))

    async def initialize_connection(self):
        """Handles initial WebSocket handshakes."""
        await self.wsocket.send(Payloads.__connect__())
        response = json.loads(await self.wsocket.recv())
        client_id = response[0]["clientId"]
        self.payloads = Payloads(self.gameid, client_id)

        # Send authentication messages
        await self.wsocket.send(self.payloads.__clientId__())
        await self.wsocket.send(self.payloads.__clientId2__())
        await self.wsocket.send(self.payloads.__connectID__(self.nickname))
        await self.wsocket.send(self.payloads.__keepInGame__())
        await self.wsocket.send(self.payloads.__metaConnect__())

    async def receiveMessages(self):
        """Receives and logs messages from the WebSocket."""
        try:
            async for message in self.wsocket:
                logger.debug(f"Received raw message: {message}")
                
                # Parse JSON
                try:
                    response = json.loads(message)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON Decode Error: {e}, message received: {message}")
                    continue  # Skip this iteration
                
                if not isinstance(response, list) or not response:
                    logger.error(f"Unexpected response format! Expected a non-empty list.")
                    continue

                first_entry = response[0]

                logger.debug(f"Parsed response: {json.dumps(first_entry, indent=2)}")
                try:
                    if (
                        first_entry["data"]["type"] == "loginResponse" and
                        first_entry["data"]["error"] == "NONEXISTING_SESSION"
                    ):
                        logger.warning(f"Warning - non-existent session")
                        raise SessionNotFoundError(f"no session found with gameid {self.gameid}")

                    if json.loads(first_entry["data"]["content"]).get("kickCode") == 1: 
                        logger.warning(f"Kicked from game, reconnecting...")
                        raise KickedFromGameError("bot kicked from game")

                    if first_entry["channel"] == "/service/player" and first_entry["data"]["id"] == 1:
                        logger.info(f"========================= Kahoot quiz incoming =========================")
                        self.sendHartebeat = False
                        await self.standAloneHeartBeat()
                        self.sendHartebeat = True
                        continue
                    if first_entry["channel"] == "/service/player" and first_entry["data"]["id"] == 2:
                        logger.debug(f"Answering the question...")
                        self.sendHartebeat = False
                        await self.standAloneHeartBeat()
                        logger.debug(json.loads(first_entry["data"]["content"]).get("type"))
                        await self.answerQuestion(random.randint(0,3), json.loads(first_entry["data"]["content"]).get("type"))
                        self.sendHartebeat = True

                    if first_entry["data"]["id"] == 13:
                        raise GameEndedError("Game ended")
                except KeyError as e:
                    logger.error(f"KeyError: {e} - Response structure may not match expectation!")
                    
        except asyncio.CancelledError:
            return

    async def heartBeat(self):
        """Sends periodic heartbeat messages to keep the connection alive."""
        try:
            while True:
                if self.sendHartebeat:
                    self.id += 1
                    self.ack += 1
                    logger.debug(f"ID is at {self.id}")
                    logger.debug(f"Sending heartbeat: {self.payloads.__heartBeat__(self.id, self.ack)}")
                    await self.wsocket.send(self.payloads.__heartBeat__(self.id, self.ack))
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            return
        
    async def standAloneHeartBeat(self):
        self.id += 1
        self.ack += 1
        await self.wsocket.send(self.payloads.__heartBeat__(self.id, self.ack))
        logger.debug(f"Sent standalone heartbeat")

    async def answerQuestion(self, choice, type):
        """Handles answering Kahoot questions."""
    
        self.id += 1
        logger.debug(f"Sending answer choice: {choice}")
        await self.wsocket.send(self.payloads.__answerQuestion__(self.id, choice, type))
        logger.info(f"Answer sent. choice: {choice}")

    async def crasher(self): 
        try:
            while True:
                logger.info("=====================crashing====================")
                logger.debug(self.payloads.__crash__(self.id))
                await self.wsocket.send(self.payloads.__crash__(self.id)) 
                await asyncio.sleep(1)
                logger.debug("here")
        except asyncio.CancelledError:
            return

    async def cleanUp(self):
        for task in self.childTasks:
            if not task.done():  # Only cancel tasks that are still running
                task.cancel()
                try:
                    await task  # Ensure graceful cancellation
                except Exception as e:
                    logger.error(f"Error during cleanup: {e}")  # Handle other unexpected errors

        self.childTasks.clear()

        if self.wsocket:
            await self.wsocket.close()

        logger.info(f"Cleanup completed, tasks canceled, WebSocket closed.")
