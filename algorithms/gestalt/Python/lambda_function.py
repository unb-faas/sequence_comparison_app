import json
import base64
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def lambda_handler(event, context):
    bd = event["body"]
    base64_message = bd
    base64_bytes = base64_message.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('ascii')
    dt = json.loads(message)
    s1 = dt["s1"]
    s2 = dt["s2"]
    return {
        'statusCode': 200,
        'body': json.dumps(similar(s1,s2))
    }
