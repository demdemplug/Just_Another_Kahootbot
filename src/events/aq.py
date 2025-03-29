from event import Event

class AQ(Event):
    channel = "service/player"

    async def handle(self, instance):
        pass