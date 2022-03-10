import json
import boto3

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        domain = event['domain']
        
        table = dynamodb.Table('ssp-website-cs')
        record = table.get_item(Key={'domain': domain})
        
        # check if the response was empty
        if not 'Item' in record.keys(): 
            raise Exception('site not found')
        
        record = record['Item']
        site_category = record['site_category']
            
        statusCode = 200
        response_body = {
            'site_category': site_category,
        }

    except Exception as err:
        statusCode = 500
        response_body = {'error': 'get_site_data: ' + str(err)}
    
    return {
        'statusCode' : statusCode,
        'body' : response_body
    }