import json
import os
import math
import dateutil.parser
import datetime
import time
import logging
import boto3
import requests
from requests_aws4auth import AWS4Auth


headers = { "Content-Type": "application/json" }
host = 'https://search-photos-zo25n66ahw2zn46y2tx3vn4pha.us-east-1.es.amazonaws.com'
region = 'us-east-1'
lex = boto3.client('lex-runtime')
credentials = boto3.Session().get_credentials()
service = 'es'
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)



def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    
    return response

    
def lambda_handler(event, context):
    print(event)
    os.environ['TZ'] = 'America/New_York'
    time.tzset()

    print("this is event:")
    print(event)
    q1 = event["queryStringParameters"]['q']
    # tmp = q1.split()
    # q1 = '+'.join(tmp)
    
    """
        
    
    """
    # q1 = event['inputTranscript']
    labels = get_labels(q1)
    if len(labels) != 0:
        img_paths = search_intent('b2-photos-storage',labels)
        response = {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin":"*","Content-Type":"application/json"},
            "body": json.dumps(img_paths),
            "isBase64Encoded": False
        }
    else:
        response = {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin":"*","Content-Type":"application/json"},
            "body": 'No Results'
        }
 
    print(response)
    return response
 
def get_labels(query):
    response = lex.post_text(
        botName='SearchPhoto',                 
        botAlias='search',
        userId="user",           
        inputText=query
    )
    print("lex-response", response)
    
    labels = []
    if 'slots' not in response:
        print("No photo collection for query {}".format(query))
    else:
        print ("slot: ",response['slots'])
        slot_val = response['slots']
        for key,value in slot_val.items():
            if value!=None:
                labels.append(value)
    return labels 


   
def dispatch(intent_request):
    #logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    intent_name = intent_request['currentIntent']['name']
    return search_intent(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')

def search_intent(bucket,labels):
    url = host+'/_search?q='
    resp = []
    for label in labels:
        print("label is")
        print(label)
        url2 = url+label
        print("url2 is")
        print(url2)
        resp.append(requests.get(url2,auth=awsauth).json())
    
    print("resp is:")
    print (resp)
    #to do wrong implementation
    output = []
    for r in resp:
        if 'hits' in r:
             for val in r['hits']['hits']:
                key = val['_source']['objectKey']
                print('key is ')
                print(key)
                if key not in output:
                    photoURL = "https://{0}.s3.amazonaws.com/{1}".format(bucket,key)
                    #todo object key with the link
                    output.append(photoURL)
    print("output is")
    print(output)

    return output

