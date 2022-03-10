import json
import boto3

dynamodb = boto3.resource('dynamodb')

# IMPORTANT: ad-exchange contains only one row: 
#   key: campaigns='active' ,
#   attributes: ids=[ids of active campaigns] 
def update_db(ids):
    try:
        table = dynamodb.Table('ad-exchange-cs')
        data = {
            'campaigns': 'active',
            'ids': ids
        }
        table.put_item(Item=data)
    except Exception as err:
        raise err

# main
def lambda_handler(event, context):
    try:
        update_db(event['ids'])
        
        statusCode = 200
        
    except:
        statusCode = 500
        
    return {
        'statusCode': statusCode
    }
    