import json
import boto3

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        id_captcha = event['id_captcha']
    
        table = dynamodb.Table('captcha-db-cs')
        search_key = {'id_captcha': id_captcha}
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
                'stars': stars
            }
        
    except Exception as err:
        statusCode = 500
        response_body = {'error': 'get_captcha: ' + str(err)}
    
    return {
        'statusCode': 200,
        'body': response_body
    }