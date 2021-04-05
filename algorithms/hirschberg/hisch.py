import json
import base64
import boto3
from alignment import Needleman, Hirschberg
import datetime

bucket_name = "sequencescomparison"
output_filename = "hirschberg-"
s3_client = boto3.client('s3')
algorithm = "Hirschberg"

def hAlign(a, b):
    h = Hirschberg()
    a,b = h.align(a,b)
    return h.score(a, b)

def lambda_handler(event, context):
    bd = event["body"]
    base64_message = bd
    base64_bytes = base64_message.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('ascii')
    dt = json.loads(message)
    _s1 = dt["s1"]
    _s2 = dt["s2"]
    id = dt["id"]
    s1 = list(_s1)
    s2 = list(_s2)
    started_at = datetime.datetime.now()
    h = Hirschberg()
    a,b = h.align(s1,s2)
    score = h.score(a, b)
    align_s1 =  a
    align_s2 =  b
    finished_at = datetime.datetime.now()
    duration =  str(finished_at - started_at)
    
    result = {
        "id":id,
        "started_at":str(started_at),
        "finished_at":str(finished_at),
        "s1":_s1,
        "s1_length":len(s1),
        "s2":_s2,
        "s2_length":len(s2),
        "duration":duration,
        "align_s1":align_s1,
        "align_s2":align_s2,
        "score":score,
        "algorithm":algorithm
    }
    
    f = open("/tmp/"+output_filename,"w+")
    f.write(json.dumps(result))
    f.close()
    s3_client.upload_file('/tmp/'+output_filename, bucket_name, output_filename+str(id)+".json")
    return {
        'statusCode': 200,
        'body': json.dumps({"result":"done"})
    }
