import json
import boto3
import requests
from datetime import datetime
from requests_aws4auth import AWS4Auth



def detectLabels(photo, bucket):
    client=boto3.client('rekognition')
    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}})
    print('rekognition', response)    
    return response

def retriveMetadata(photo, bucket):
    client = boto3.client('s3')
    response = client.head_object(Bucket=bucket, Key=photo)
    return response['Metadata']
    
    
def parseForES(bucket, photo, labels):

    jsonObject = {
        "objectKey" : photo,
        "bucket" : bucket,
        "createdTimeStamp" : datetime.now().strftime("%y-%m-%d %H:%M:%S"), #"2020-05-02 17:32:55",
        "labels" : labels
        
    }
    return jsonObject
    
def indexToES(document):
    host = "https://search-photos-zo25n66ahw2zn46y2tx3vn4pha.us-east-1.es.amazonaws.com/photos/_doc"
    index = "photos"

    region = 'us-east-1'
    service = 'es'
    headers = { "Content-Type": "application/json" }
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    # print(url)
    response = requests.post(host, auth=awsauth, json=document, headers=headers)
    print("response", response)
    
    return response
    
def lambda_handler(event, context):
    print("event is")
    print(event)
    records = event['Records']
    
    for record in records:
        print("record", record)
    
    
    bucket = event['Records'][0]["s3"]["bucket"]["name"]
    photo = event['Records'][0]["s3"]["object"]["key"]
    labels = detectLabels(photo, bucket)
    metadata = retriveMetadata(photo, bucket)
    if 'customlabels' in metadata.keys():
        a1 = [metadata['customlabels']]
    else:
        a1 = []
            
    for i in range(len(labels['Labels'])):
        a1.append(labels['Labels'][i]['Name'])

    
    document = parseForES(bucket, photo, a1)
    print("document is", document)
    response = indexToES(document)
    print("the response on 80 is ", response)
    data = json.loads(response.content.decode('utf-8'))
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
