from asyncore import ExitNow
from fastapi import FastAPI
import json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from alignment import Hirschberg
import datetime
import asyncio
from concurrent.futures.process import ProcessPoolExecutor
from fastapi import FastAPI
import time
from azure.storage.blob import BlobServiceClient
import os

algorithm = "hirschberg"
output_filename = "hirschberg-"

def hAlign(a, b):
    h = Hirschberg()
    a,b = h.align(a,b)
    return h.score(a, b)

def align( event ):
    tempPath = "/tmp/"
    _s1 = event["s1"]
    _s2 = event["s2"]
    _t1 = event["t1"]
    _t2 = event["t2"]
    _service = event["service"]
    _concurrence = event["concurrence"]
    _repetition = event["repetition"]
    id = event["execid"]
    s1 = list(_s1)
    s2 = list(_s2)
    started_at = datetime.datetime.now()
    container_name = event["container"]
    storage_account_string_connection = event["storageConnection"]
    blob_service_client = BlobServiceClient.from_connection_string(storage_account_string_connection)

    blob = blob_service_client.get_container_client(container_name)
    if not blob.exists():
        blob_service_client.create_container(container_name)
    
    result = {
        "id":id,
        "service":_service,
        "started_at":str(started_at),
        "s1": {"content":_s1, "title":_t1, "length":len(s1)},
        "s2": {"content":_s2, "title":_t2, "length":len(s2)},
        "algorithm":algorithm
    }
    
    local_id = "%.20f" % time.time()
    _output_path = _service + "/repetition_" + _repetition + "/concurrence_" + _concurrence + "/"
    _output_filename = output_filename + str(id) + "_" + str(local_id) + ".json"

    f = open(tempPath+_output_filename,"w+")
    f.write(json.dumps(result))
    f.close()

    upload_file_path = os.path.join(tempPath, _output_filename)

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=_output_path+_output_filename)
    with open(upload_file_path, "rb") as data:
            blob_client.upload_blob(data)

    h = Hirschberg()
    a,b = h.align(s1,s2)
    score = h.score(a, b)

    align_s1 =  a
    align_s2 =  b
    finished_at = datetime.datetime.now()
    duration =  str(finished_at - started_at)
    
    result = {
        "id":id,
        "service":_service,
        "started_at":str(started_at),
        "finished_at":str(finished_at),
        "s1": {"content":_s1, "title":_t1, "length":len(s1),"align":align_s1},
        "s2": {"content":_s2, "title":_t2, "length":len(s2),"align":align_s2},
        "duration":duration,
        "score":score,
        "algorithm":algorithm
    }
    f = open(tempPath+_output_filename,"w+")
    f.write(json.dumps(result))
    f.close()

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=_output_path+_output_filename)
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    return {
        'statusCode': 200,
        'body': json.dumps({"result":"done"})
    }

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    execid: str
    repetition: str
    concurrence: str
    s1: str
    s2: str
    t1: str
    t2: str
    service: str
    container: str
    storageConnection: str
    
async def run_in_process(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(app.state.executor, fn, *args)

@app.put("/localhost")
async def play(item: Item):
    res = await run_in_process(align, {
                                        "execid":item.execid, 
                                        "repetition":item.repetition,
                                        "concurrence":item.concurrence,
                                        "s1":item.s1,
                                        "s2":item.s2,
                                        "t1":item.t1,
                                        "t2":item.t2,
                                        "service":item.service,
                                        "container":item.container,
                                        "storageConnection": item.storageConnection,
                                      })
    return {"result": res}


@app.on_event("startup")
async def on_startup():
    app.state.executor = ProcessPoolExecutor()


@app.on_event("shutdown")
async def on_shutdown():
    app.state.executor.shutdown()
