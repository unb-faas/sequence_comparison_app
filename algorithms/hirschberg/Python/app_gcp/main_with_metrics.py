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
import os, psutil, platform

output_filename = "hirschberg-"
s3_client = boto3.client('s3')
algorithm = "Hirschberg"
bucket = "sequencecomparisson"
region = "us-west-1"

_proc_status = '/proc/%d/status' % os.getpid()

_scale = {'kB': 1024.0, 'mB': 1024.0*1024.0,
          'KB': 1024.0, 'MB': 1024.0*1024.0}

def _VmB(VmKey):
    '''Private.
    '''
    global _proc_status, _scale
     # get pseudo file  /proc/<pid>/status
    try:
        t = open(_proc_status)
        v = t.read()
        t.close()
    except:
        return 0.0  # non-Linux?
     # get VmKey line e.g. 'VmRSS:  9999  kB\n ...'
    i = v.index(VmKey)
    v = v[i:].split(None, 3)  # whitespace
    if len(v) < 3:
        return 0.0  # invalid format?
     # convert Vm value to bytes
    return float(v[1]) * _scale[v[2]]


def memory(since=0.0):
    '''Return memory usage in bytes.
    '''
    return _VmB('VmSize:') - since


def resident(since=0.0):
    '''Return resident memory usage in bytes.
    '''
    return _VmB('VmRSS:') - since


def stacksize(since=0.0):
    '''Return stack size in bytes.
    '''
    return _VmB('VmStk:') - since

def create_bucket(bucket_name, region=None):
    """Create an S3 bucket in a specified region

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-1).

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """

    # Create bucket
    try:
        if region is None:
            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration=location)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def calc_metrics_variance(before, after):
    variance = {}
    for key in after:
        variance[key] = {}
        for item_key in after[key]:
            try:
                variance[key][item_key] = float(after[key][item_key]) - float(before[key][item_key])
            except:
                variance[key][item_key] = after[key][item_key]
    return variance


def hAlign(a, b):
    h = Hirschberg()
    a,b = h.align(a,b)
    return h.score(a, b)

def getMetrics():
    memory1 = dict(psutil.virtual_memory()._asdict())
    memory2 = dict({"vmb_used_memory":memory()})
    memory3 = dict({"vmb_stack_memory":stacksize()})
    memory3 = dict({"vmb_resident_memory":resident()})
    cpu1 = dict(psutil.cpu_freq(percpu=False)._asdict())
    cpu2 = dict(psutil.cpu_stats()._asdict())
    cpu3 = dict(psutil.cpu_times()._asdict())
    cpu = {**cpu1, **cpu2, **cpu3}
    mem = {**memory1, **memory2, **memory3}
    return {"memory":mem, "cpu":cpu, "platform":platform.uname()._asdict()}

def align( event, context, testType, bucket):
    metrics_before = getMetrics()
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
    _type = testType
    id = dt["id"]
    s1 = list(_s1)
    s2 = list(_s2)
    started_at = datetime.datetime.now()
    
    result = {
        "id":id,
        "type":_type,
        "metrics":{"before":metrics_before},
        "started_at":str(started_at),
        "s1": {"content":_s1, "title":_t1, "length":len(s1)},
        "s2": {"content":_s2, "title":_t2, "length":len(s2)},
        "algorithm":algorithm
    }
    _output_filename = output_filename + str(id)
    f = open("/tmp/"+_output_filename,"w+")
    f.write(json.dumps(result))
    f.close()
    s3_client.upload_file('/tmp/'+_output_filename, bucket, _output_filename+".json")
    
    h = Hirschberg()
    a,b = h.align(s1,s2)
    score = h.score(a, b)

    metrics_after = getMetrics()

    align_s1 =  a
    align_s2 =  b
    finished_at = datetime.datetime.now()
    duration =  str(finished_at - started_at)
    
    result = {
        "id":id,
        "type":_type,
        "metrics":{"before":metrics_before, "after":metrics_after, "variance":calc_metrics_variance(metrics_before,metrics_after)},
        "started_at":str(started_at),
        "finished_at":str(finished_at),
        "s1": {"content":_s1, "title":_t1, "length":len(s1),"align":align_s1},
        "s2": {"content":_s2, "title":_t2, "length":len(s2),"align":align_s2},
        "duration":duration,
        "score":score,
        "algorithm":algorithm
    }
    f = open("/tmp/"+_output_filename,"w+")
    f.write(json.dumps(result))
    f.close()
    s3_client.upload_file('/tmp/'+_output_filename, bucket, _output_filename+".json")
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
    bucket: str
    testType: str

@app.put("/")
def play(item: Item):
    create_bucket(item.bucket)
    return align({"body":item.base64}, "", item.testType, item.bucket)
