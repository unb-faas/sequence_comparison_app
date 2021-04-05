from typing import Optional
from fastapi import FastAPI
import boto3
import json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import base64
from alignment import Hirschberg
import datetime
import logging
from botocore.exceptions import ClientError
import asyncio
from concurrent.futures.process import ProcessPoolExecutor
from fastapi import FastAPI

output_filename = "hirschberg-"
s3_client = boto3.client('s3')
algorithm = "Hirschberg"
bucket = "sequencecomparisson"
region = "us-west-1"

def hAlign(a, b):
    h = Hirschberg()
    a,b = h.align(a,b)
    return h.score(a, b)

def align( event ):
    tempPath = "/dev/shm/"
    bd = event["body"]
    base64_message = bd
    base64_bytes = base64_message.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('ascii')
    dt = json.loads(message)
    _s1 = dt["s1"]
    _s2 = dt["s2"]
    _t1 = dt["t1"]
    _t2 = dt["t2"]
    _type = dt["type"]
    _concurrence = dt["concurrence"]
    id = dt["id"]
    s1 = list(_s1)
    s2 = list(_s2)
    started_at = datetime.datetime.now()
    
    result = {
        "id":id,
        "type":_type,
        "started_at":str(started_at),
        "s1": {"content":_s1, "title":_t1, "length":len(s1)},
        "s2": {"content":_s2, "title":_t2, "length":len(s2)},
        "algorithm":algorithm
    }

    _output_filename = output_filename + str(id)
    _output_path = _type+"/"+_concurrence+"/"
    f = open(tempPath+_output_filename,"w+")
    f.write(json.dumps(result))
    f.close()
    s3_client.upload_file(tempPath+_output_filename, bucket, _output_path+_output_filename+".json")
    
    h = Hirschberg()
    a,b = h.align(s1,s2)
    score = h.score(a, b)

    align_s1 =  a
    align_s2 =  b
    finished_at = datetime.datetime.now()
    duration =  str(finished_at - started_at)
    
    result = {
        "id":id,
        "type":_type,
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
    s3_client.upload_file(tempPath+_output_filename, bucket, _output_path+_output_filename+".json")
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
    base64: str

async def run_in_process(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(app.state.executor, fn, *args)

@app.put("/localhost")
async def play(item: Item):
    #return align({"body":item.base64})
    res = await run_in_process(align, {"body":item.base64})
    return {"result": res}


@app.on_event("startup")
async def on_startup():
    app.state.executor = ProcessPoolExecutor()


@app.on_event("shutdown")
async def on_shutdown():
    app.state.executor.shutdown()