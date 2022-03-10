import json
import boto3
import random

dynamodb = boto3.resource('dynamodb')
N_DEFAULT = 1

def lambda_handler(event, context):
    try:
        table = dynamodb.Table('captcha-db-cs')
        
        # get random id of default capctha
        random_n = random.randint(0, N_DEFAULT-1)
        random_id_tmp = "default-{n}-captchastar.com"
        random_id = random_id_tmp.format(n=random_n)

        # get captcha from db
        search_key = {'id_captcha': random_id}
        record = table.get_item(Key=search_key)
        
        # check if the response was empty
        if not 'Item' in record.keys(): 
           raise Exception('captcha not found') # dovrebbe tornare un captcha di default
        else:
            # retrieve data
            captcha_data = record['Item']
            stars = captcha_data['stars']
            
            statusCode = 200
            response_body = {
                'stars': stars,
                'id_captcha': random_id
            }
        
    except Exception as err:
        statusCode = 500
        response_body = {'error': 'get_captcha: ' + str(err)}
    
    return {
        'statusCode': 200,
        'body': response_body
    }