import re
import requests
import subprocess
import base64
import asyncio
import websockets
import random
import uuid
import json
import time
import os
from pathlib import Path
from .payloads import Payloads
from .exceptions import *

YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
MAGENTA = "\033[35m"


def runchallenge(challenge_code: str, token) -> str:
    """Runs a JavaScript challenge for authentication."""
    challenge_code = 'console.log(' + challenge_code[:121] + ')' + challenge_code[121:]
    challenge_code = re.sub(r'this', 'a', challenge_code)
    
    challenge_script = open(Path(__file__).parent / "../challenge/angular.js").read() + challenge_code
    challenge_file = Path(__file__).parent / "../challenge/challenge.js"
    challenge_file.write_text(challenge_script)

    result = subprocess.run(['node', challenge_file], capture_output=True, text=True)
    challenge = result.stdout.strip()
    print(f"{CYAN}Challenge output: {challenge}{RESET}")
    result = ""
    for c1, c2 in zip(challenge, base64.b64decode(token).decode('utf-8', 'strict')):
        result += chr(ord(c1) ^ ord(c2))

    return result


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
            await self.connect() # connect will create the child tasks
            
            while True:
                for task in self.childTasks:
                    if task.done():
                        if isinstance(task.exception(), Handler):
                            await self.errorHandler.put((self, task.exception()))
                            print(f"{RED}watchDog: {task.exception()}{RESET}")
                            return
                        
                        print(f"{RED}watchDog: {task.exception()}{RESET}")
                            
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("something happend: ", e)
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
            challenge_response = runchallenge(response.json()['challenge'], response.headers['x-kahoot-session-token'])
        except Exception as e:
            print(f"{RED}Failed to fetch challenge: {e}{RESET}")
            return

        print(f"{GREEN}WebSocket URL: wss://kahoot.it/cometd/{self.gameid}/{challenge_response}{RESET}")

        print(f"{CYAN}Connecting to WebSocket...{RESET}")
        self.wsocket = await websockets.connect(
            f'wss://kahoot.it/cometd/{self.gameid}/{challenge_response}',
            ping_interval=30, 
            ping_timeout=60 
        )
        print(f"{GREEN}Connected!{RESET}")
        await self.initialize_connection()
        self.childTasks.append(asyncio.create_task(self.heartBeat()))
        self.childTasks.append(asyncio.create_task(self.receiveMessages()))
        print("=========================crash=========================", self.crash)
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

    # dont get mad at me i have not made the classes for it yet i am just doing testing
    async def receiveMessages(self):
        """Receives and logs messages from the WebSocket."""
        try:
            async for message in self.wsocket:
                print(f"{CYAN}Received raw message: {message}{RESET}", flush=True)  # Debugging log
                
                # Parse JSON
                try:
                    response = json.loads(message)
                except json.JSONDecodeError as e:
                    print(f"{RED}JSON Decode Error: {e}, message received: {message}{RESET}")
                    continue  # Skip this iteration
                
                if not isinstance(response, list) or not response:
                    print(f"{RED}Unexpected response format! Expected a non-empty list.{RESET}")
                    continue

                first_entry = response[0]

                # Debugging: Log structure
                print(f"{MAGENTA}Parsed response: {json.dumps(first_entry, indent=2)}{RESET}")
                try:
                    if (
                        first_entry["data"]["type"] == "loginResponse" and
                        first_entry["data"]["error"] == "NONEXISTING_SESSION"
                    ):
                        print(f"{YELLOW}Warning - non-existent session {RESET}")
                        raise SessionNotFoundError(f"no session found with gameid {self.gameid}")

                    if json.loads(first_entry["data"]["content"]).get("kickCode") == 1: 
                        print(f"{YELLOW}Kicked from game, reconnecting...{RESET}")
                        raise KickedFromGameError("bot kicked from game")

                    if first_entry["channel"] == "/service/player" and first_entry["data"]["id"] == 1:
                        print(f"{GREEN}========================= Kahoot quiz incoming ========================={RESET}")
                        self.sendHartebeat = False
                        await self.standAloneHeartBeat()
                        self.sendHartebeat = True
                        continue
                    if first_entry["channel"] == "/service/player" and first_entry["data"]["id"] == 2:
                        print(f"{MAGENTA}Answering the question...{RESET}")
                        self.sendHartebeat = False
                        await self.standAloneHeartBeat()
                        print(json.loads(first_entry["data"]["content"]).get("type"))
                        await self.answerQuestion(random.randint(0,3), json.loads(first_entry["data"]["content"]).get("type"))
                        self.sendHartebeat = True


                    if first_entry["data"]["id"] == 13:
                        raise GameEndedError("Game ended")
                except KeyError as e:
                    print(f"{RED}KeyError: {e} - Response structure may not match expectation!{RESET}", flush=True)
                    
        except asyncio.CancelledError:
            return

    async def heartBeat(self):
        """Sends periodic heartbeat messages to keep the connection alive."""
        try:
            while True:
                if self.sendHartebeat:
                    self.id += 1
                    self.ack += 1
                    print(f"{YELLOW}ID is at {self.id}{RESET}")
                    print(f"{CYAN}Sending heartbeat: {self.payloads.__ezFlooder__(self.id, self.ack)}{RESET}")
                    await self.wsocket.send(self.payloads.__ezFlooder__(self.id, self.ack))
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            return
        
    async def standAloneHeartBeat(self):
        self.id += 1
        self.ack += 1
        await self.wsocket.send(self.payloads.__ezFlooder__(self.id, self.ack))
        print(f"{CYAN}Sent standalone heartbeat{RESET}")

    async def answerQuestion(self, choice, type):
        """Handles answering Kahoot questions."""
    
        self.id += 1
        print(f"{MAGENTA}Sending answer choice: {choice}{RESET}")
        await self.wsocket.send(self.payloads.__answerQuestion__(self.id, choice, type))
        print(f"{GREEN}Answer sent. choice: {choice}{RESET}")

    async def crasher(self): 
        try:
            while True:
                print("=====================crashing====================")
                print(self.payloads.__crash__(self.id))
                await self.wsocket.send(self.payloads.__crash__(self.id)) # sending ansers repetly when there is nothing to anser crashes the entire game 
                await asyncio.sleep(1)
                print("here")
        except asyncio.CancelledError:
            return
    

    async def cleanUp(self):
        
        for task in self.childTasks:
            if not task.done():  # Only cancel tasks that are still running
                task.cancel()
                try:
                    await task  # Ensure graceful cancellation
                except Exception as e:
                    print(f"Error during cleanup: {e}")  # Handle other unexpected errors

        self.childTasks.clear()


        if self.wsocket:
            await self.wsocket.close()

        print(f"{YELLOW}Cleanup completed, tasks canceled, WebSocket closed.{RESET}")
