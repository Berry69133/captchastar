import json
import joblib
import numpy as np
import boto3
from io import BytesIO

BUCKET_NAME = 'lambda-upload-cs'
MODEL_PATH = 'dsp_bidding.joblib'

# get model from S3 bucket
s3 = boto3.resource("s3")
with BytesIO() as data:
    s3.Bucket(BUCKET_NAME).download_fileobj(MODEL_PATH, data)
    data.seek(0)
    model = joblib.load(data)
    
def category_to_label(site_category):
    category_map = {
        'other': 0,
        'sport': 1,
        'clothing': 2,
        'technology': 3,
        'entertainment': 4,
        'financial': 5,
        'news': 6,
        'health & beauty': 7,
        'food': 8
    }
    
    site_category = site_category.lower()
    if site_category not in category_map.keys():
        # during development
        raise Exception('category_to_label : category not supported')
        # during production
        # return 0
    else:
        return category_map[site_category]
    
def lambda_handler(event, context):
    # COSA BRUTTA DA TOGLIERE, STIAMO METTENDO TUTTI I SITE_ID A 0
    event['site_id'] = 0
    event['ad_id'] = 0
    
    try:
        # convert string site category to labels supported by model
        category_label = category_to_label(event['site_category']) 
        event['site_category'] = category_label
        
        # dict to numpy array suitable for prediction transformations
        sample = list(map(int, event.values()))
        sample = np.array(sample) 
        sample = sample.reshape(1, -1)
        
        # estimate ctr
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
