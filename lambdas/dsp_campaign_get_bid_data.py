import json
import boto3

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# decode the lambda return 
def decode_stream(response_stream):
    response_data = response_stream['Payload'].read()
    response_data = json.loads(response_data)
    if response_data['statusCode'] == 200:
        return response_data['body']
    else:
        raise Exception(response_data['body']['error'])

def lambda_handler(event, context):
    try:
        id_campaign = event['id_campaign']
        
        table = dynamodb.Table('dsp-campaign-cs')
        record = table.get_item(Key={'id_campaign': id_campaign})
    
        # 1- check if the response was empty => no match in campaign id
        if not 'Item' in record.keys(): 
            # default values => do not partecipate in the auction
            id_captcha = -1
            ecpc = -1
            stars = ""
            id_advertiser = -1
        else:
            campaign_data = record['Item']
            id_captcha = campaign_data['id_captcha']
            ecpc = campaign_data['ecpc']
            id_advertiser = campaign_data['id_advertiser']
                
            statusCode = 200
            response_body = {
                'id_captcha': id_captcha,
                'ecpc': ecpc,
                'id_advertiser': id_advertiser
            }
            
    except Exception as err:
        statusCode = 500
        response_body = {'error': 'get_bid_data: ' + str(err)}
    
    return {
        'statusCode' : statusCode,
        'body' : response_body
    }