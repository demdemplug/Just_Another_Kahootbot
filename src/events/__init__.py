import importlib
import os
from pydantic import BaseModel
from typing import Dict
from .event import Event
import json

event_classes: Dict[str, [BaseModel]] = {}

events_dir = os.path.dirname(__file__) 

for filename in os.listdir(events_dir):
    if filename.endswith(".py") and filename != "__init__.py" and filename != "event.py":
        module_name = f".{filename[:-3]}"  
        module = importlib.import_module(module_name, package=__name__)
            
        for attr_name in dir(module):
            
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseModel) and issubclass(attr, Event) and attr not in (BaseModel, Event):
                if not "channel" in attr.model_fields:
                    print(f"warning: class {attr} does not have a channel type... skiping")
                    continue
                print(attr.__fields__.keys())
            
                channel = attr.model_fields["channel"].default
                
                if event_classes.get(channel, None):
                    event_classes[channel].append(attr)

                else: 
                    event_classes[channel] = [attr]               
                

stuff = json.dumps({
    "channel": "booyu",
    "whhww": "retard",
    "wadwr": 1
}) 
stuff = json.loads(stuff)

for event in event_classes[stuff["channel"]]:
    if event.__fields__.keys() == stuff.keys():
        event = event.parse_obj(stuff)
        
        break


print(type(event))