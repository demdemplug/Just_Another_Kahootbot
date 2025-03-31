from pydantic import BaseModel, model_validator
from typing import List, Optional
from .bases import Event
import orjson

# Models for nested structures

class AvailableCollaborations(BaseModel):
    isAutoAssign: bool
    canRename: bool
    data: List
    collaborationNameLocale: str

class Content(BaseModel):
    data: dict
    stableIdentifier: str
    isHighContrast: bool
    teamMembers: List
    loginState: int
    didControllerLeave: bool
    avatarTimestamp: Optional[int] = None
    wasControllerKicked: bool
    state: int
    availableCollaborations: AvailableCollaborations
    chosenCollaborationIndex: int
    kahootLangIsRTL: bool
    canChangeAvatar: bool
    youtubeAPIKey: str
    userReactionsEnabled: bool
    islandData: Optional[dict] = None
    audienceQuestionsData: Optional[dict] = None

class Ext(BaseModel):
    timetrack: int

class Data(BaseModel):
    gameid: str
    host: str
    id: int
    type: str
    content: Content
    cid: str

class ServicePlayerEventV4(Event):
    ext: Ext
    data: Data
    channel: str = "/service/player"
    
    # Model validator to convert the content field from a string to a Content object
    @model_validator(mode='before')
    def check_required_fields(cls, values: dict) -> dict:
        content = values.get('data', {}).get('content', None)
        
        if isinstance(content, str):
            try:
                parsed_content = orjson.loads(content)
                values["data"]["content"] = Content(**parsed_content)
            except orjson.JSONDecodeError:
                raise ValueError(f"Failed to parse content as JSON: {content}")
        return values
    
    # Async handle method (placeholder for your logic)
    async def handle(self, instance):
        pass

# {
#   "ext": {
#     "timetrack": 1743294365442
#   },
#   "data": {
#     "gameid": "21801",
#     "host": "play.kahoot.it",
#     "id": 17,
#     "type": "message",
#     "content": {
#       "data": {},
#       "stableIdentifier": "5fe80985-8094-42d7-9428-2865ffa3d936-388",
#       "isHighContrast": false,
#       "teamMembers": [],
#       "loginState": 3,
#       "didControllerLeave": false,
#       "avatarTimestamp": null,
#       "wasControllerKicked": false,
#       "state": 0,
#       "availableCollaborations": {
#         "isAutoAssign": false,
#         "canRename": true,
#         "data": [],
#         "collaborationNameLocale": "en"
#       },
#       "chosenCollaborationIndex": -1,
#       "kahootLangIsRTL": false,
#       "canChangeAvatar": false,
#       "youtubeAPIKey": "AVPnqKsYCBOYXOT2K-tkdt2hlNNHQ7WYvIas3tvpb4U9TMyhDzrJw6bYFBwqAUF6kzC3N-ShGzrn7fzuG19hqEX-Eii35wr0wwUc-K8bMqdJhXDzSDRCPl0U2iCs8oWVvPmmheELqHBoMuBCdfsyIHo98JybvjdFvA==",
#       "userReactionsEnabled": false,
#       "islandData": null,
#       "audienceQuestionsData": null
#     },
#     "cid": "1320022017"
#   },
#   "channel": "/service/player"
# }
