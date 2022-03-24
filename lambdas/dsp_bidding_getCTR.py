import json
import joblib
import numpy as np
import boto3
from io import BytesIO

BUCKET_NAME = 'lambda-upload-cs'

# get model from S3 bucket
s3 = boto3.resource('s3')
lambda_client = boto3.client('lambda')

# decode the lambda return 
def decode_stream(response_stream):
    response_data = response_stream['Payload'].read()
    response_data = json.loads(response_data)
    if response_data['statusCode'] == 200:
        return response_data['body']
    else:
        raise Exception(response_data['body']['error'])

def get_model(id_advertiser):
    model_name = id_advertiser + ".model.joblib"
    model_path = "ctr_models/" + model_name
    
    with BytesIO() as data:
        s3.Bucket(BUCKET_NAME).download_fileobj(model_path, data)
        data.seek(0)
        model = joblib.load(data)
        
    return model

def get_encoded_feats(domain, region, city, os, browser, id_advertiser): # id_advertiser should be removed in the final version 
    try:
        payload = json.dumps({'id_advertiser': id_advertiser}) # the output is randomly generated, so we do not use the input parameters currently
        response = lambda_client.invoke(FunctionName='dsp_encode_slot_data', Payload=payload)
        response = decode_stream(response)
        response = response['encoded_features']
        if response: # check if the response is not empty
            region = response['region']
            city = response['city']
            domain = response['domain']
            os = response['os']
            browser = response['browser']
            return domain, region, city, os, browser
            
        else: 
            raise Exception
            
    except Exception as err:
        raise Exception('get encoded features: ' + str(err))

def lambda_handler(event, context):
    try:
        id_advertiser = event['id_advertiser']
        slot_data = event['slot_data']
        
        # TODO: handle site_data here
        
        # get one-hot encoded version of categorical features
        site_id, region, city, os, browser = get_encoded_feats(slot_data['site_id'], slot_data['region'], slot_data['city'], slot_data['os'], slot_data['browser'], id_advertiser) # id_advertiser should be removed in the final version 
        
        # create sample suitable for CTR prediction
        hour = int(slot_data['hour'])
        weekday = int(slot_data['weekday'])
        sample = [weekday, hour, *os, *browser, *site_id, *city, *region] 
        sample = np.array(sample) 
        sample = sample.reshape(1, -1)
        
        # estimate ctr
        model = get_model(id_advertiser)
        probs = model.predict_proba(sample)
        ctr = probs[0,1] # for the first and only sample (0) get probability of being of class 1 (click) 
        
        statusCode = 200
        response_body = {'ctr' : ctr}
        
    except Exception as err:
        statusCode = 500
        response_body = {'error': 'get_CTR : ' + str(err)}
    
    return {
        'statusCode': statusCode,
        'body': response_body
    }
