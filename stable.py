# import requests
# import uuid
# import time
# import subprocess
# import re
# import base64
# import websockets
# import json
# from src.payloads import Payloads
# import asyncio
# import random
# from quart import Quart, request, jsonify
# from typing import List, Coroutine

# # funny javascript challenge runner 
# def runchallenge(challenge_code: str) -> str:
    
#     challenge_code = 'console.log(' + challenge_code[:121] + ')' + challenge_code[121:]

#     challenge_code = re.sub(r'this', 'a', challenge_code)

#     challenge_code = open('angular.js', 'r').read() + challenge_code

#     open('challenge.js', 'w').write(challenge_code)

#     result = subprocess.run(['node', 'challenge.js'], capture_output=True, text=True)

#     return result.stdout.strip()


# def xorStrings(challenge, token) -> str:
#     result = ""
#     for c1, c2 in zip(challenge, base64.b64decode(token).decode('utf-8', 'strict')):
#         result += chr(ord(c1) ^ ord(c2))

#     return result



# class KahootBot:
#     payloads: Payloads
#     gameid: str
#     wsocket: websockets
#     ack: int
#     id: int

#     def __init__(self, gameid: int, nickname: str):
#         self.gameid = gameid
#         self.nickname = nickname + str(random.randint(999999, 9999999))  # testing
#         self.ack = 2
#         self.id = 6

#     async def connect(self):
#         cookies = {
#             "generated_uuid": str(uuid.uuid4()),
#             "player": "active"
#         }
#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"
#         }

#         r = requests.get(f'https://kahoot.it/reserve/session/{self.gameid}/?{time.time()}', headers=headers, cookies=cookies)
#         solvedChallenge = xorStrings(runchallenge(r.json()['challenge']), r.headers['x-kahoot-session-token'])

#         print("Connecting to WebSocket...")
#         self.wsocket = await websockets.connect(f'wss://kahoot.it/cometd/{self.gameid}/{solvedChallenge}')
#         print("Connected!")

#         await self.wsocket.send(Payloads.__connect__())
#         cid = json.loads(await self.wsocket.recv())[0]["clientId"]
#         self.payloads = Payloads(self.gameid, cid)

#         # Sending initial payloads
#         await self.wsocket.send(self.payloads.__clientId__())
#         await self.wsocket.send(self.payloads.__clientId2__())
#         # await self.wsocket.send(self.payloads.__clientId3__())

#         # Send meta connection and keep-alive
#         await self.wsocket.send(self.payloads.__connectID__(self.nickname))
#         await self.wsocket.send(self.payloads.__keepInGame__())
#         await self.wsocket.send(self.payloads.__metaConnect__())

#         # Start the message listener 
#         # TODO we need to like accually have this anser stuff
#         # self.receive_task = asyncio.create_task(self.receive_messages())

#         # Start the heartbeat in the background
#         self.heartbeat_task = asyncio.create_task(self.heartBeat())
        
#         try:
#             # main task runtime. waiting keeps it alive it can also call other functions like a crasher or run the anser thingy so yay
#             while True:
#                 self.id += 1
#                 await self.wsocket.send(self.payloads.__answerQuestion__(self.id, 0))
#                 await asyncio.sleep(1)
#         except asyncio.CancelledError:
#             print(f"Bot {self.nickname} connection closed.")
#             await self.wsocket.close()
#             self.heartbeat_task.cancel()
#             raise

    
    
#     async def receive_messages(self):
#         """Dedicated coroutine to receive messages without conflicts."""
#         try:
#             async for message in self.wsocket:
#                 print(f"Received: {message}")
#         except websockets.exceptions.ConnectionClosed:
#             print("WebSocket closed.")

#     async def heartBeat(self):
#         """Handles sending heartbeat messages."""
#         while True:
#             self.id += 1
#             self.ack += 1
#             await self.wsocket.send(self.payloads.__ezFlooder__(self.id, self.ack))
#             await asyncio.sleep(30)

#     async def answer_question(self, choice):
#         """Handles answering a Kahoot question."""
#         self.ack += 1
#         self.id += 1
#         await self.wsocket.send(self.payloads.__answerQuestion__(self.id, choice))
#         print("Answer sent.")



# import hypercorn.asyncio
# from hypercorn.config import Config

# class Swarm:
#     def __init__(self, ttl: int):
#         self.ttl = int(ttl)
#         self.start_time = time.time()
#         self.tasks: List[asyncio.Task] = []

#     def isAlive(self) -> bool:
#         """Check if the swarm is still alive based on TTL."""
#         return (time.time() - self.start_time) < self.ttl

#     async def runTasks(self, coroutines: List[Coroutine]):
#         """Start the tasks asynchronously."""
#         print("running the tasks")
#         self.tasks = [asyncio.create_task(task) for task in coroutines]
#         # await asyncio.gather(*self.tasks)

#     async def closeTasks(self):
#         """Cancel all running tasks."""
#         for task in self.tasks:
#             task.cancel()
#             try:
#                 await task  # Ensure graceful cancellation
#             except asyncio.CancelledError:
#                 pass  

#     async def main(self, coroutines: List[Coroutine]):
#         """Main task runner with TTL check."""
#         await self.runTasks(coroutines)
#         while any(not task.done() for task in self.tasks):
#             if not self.isAlive():
#                 await self.closeTasks()
#                 print("Closing tasks due to TTL expiration")
#                 break
#             await asyncio.sleep(1)  # Avoid busy waiting

#     def start(self, coroutines: List[Coroutine]):
#         """Start the swarm in an async event loop."""
#         asyncio.create_task(self.main(coroutines))

# app = Quart(__name__)
# swarms: List[Swarm] = []

# @app.route('/swarm', methods=['POST'])
# async def swarm():
#     data = await request.json
#     amount = data.get('amount')
#     gamepin = data.get('gamepin')
#     nickname = data.get('nickname')
#     ttl = data.get('ttl')

#     if not all([amount, gamepin, nickname, ttl]):
#         return jsonify({"error": "Missing parameters"}), 400
    
#     # Create the coroutines
#     coroutines: List[Coroutine] = [KahootBot(gamepin, nickname).connect() for _ in range(int(amount))]
    
#     # Create and start the swarm
#     swarm = Swarm(ttl)
#     swarm.start(coroutines)
#     print("what the fuck is happining")
#     swarms.append(swarm)

#     return jsonify({"message": "Swarm created and tasks started"}), 200


# async def start():
#     config = Config()
#     await hypercorn.asyncio.serve(app, config)

# if __name__ == '__main__':
#     asyncio.run(start())
