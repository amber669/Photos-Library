import json
import boto3
# from botocore.vendored import requests
import requests
from datetime import datetime
from requests_aws4auth import AWS4Auth



def detectLabels(photo, bucket):
    client=boto3.client('rekognition')
    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}})
    print('rekognition', response)
    # "MaxLabels": 10, "MinConfidence": 75 (Optional?)
    
    return response

def retriveMetadata(photo, bucket):
    client = boto3.client('s3')
    response = client.head_object(Bucket=bucket, Key=photo)
    #to do where to handle custom label?
    print("the metadata is ")
    print(response['Metadata'])
    return response['Metadata']
    
    
def parseForES(bucket, photo, labels):
    # labels = []
    
    # for rec in resources['Labels']:
    #     labels.append(rec['Name'])
    jsonObject = {
        "objectKey" : photo,
        "bucket" : bucket,
        "createdTimeStamp" : datetime.now().strftime("%y-%m-%d %H:%M:%S"), #"2020-05-02 17:32:55",
        "labels" : labels
        
    }
    return jsonObject
    
def indexToES(document):
    host = "https://search-photos-zo25n66ahw2zn46y2tx3vn4pha.us-east-1.es.amazonaws.com/photos/_doc"
    # host = "https://search-searchphoto2-7cg5u7mox3a5md4ddbjemlscpe.us-east-1.es.amazonaws.com"
    index = "photos"
    # url = host + '/' + index + '/' + 'lambda-type'
    # url = host + '/' + index
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
    print("photo is ", photo)
    labels = detectLabels(photo, bucket)
    print('labels', labels)
    metadata = retriveMetadata(photo, bucket)
    if 'customlabels' in metadata.keys():
        a1 = [metadata['customlabels']]
    else:
        a1 = []
            
    for i in range(len(labels['Labels'])):
        a1.append(labels['Labels'][i]['Name'])
    print("the labesl in total")
    print(a1)
    
    
    document = parseForES(bucket, photo, a1)
    print("document is", document)
    response = indexToES(document)
    print("the response on 80 is ", response)
    data = json.loads(response.content.decode('utf-8'))
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
