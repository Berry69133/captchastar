import json
import boto3

lambda_client = boto3.client('lambda')

# decode the lambda return 
def decode_stream(response_stream):
    response_data = response_stream['Payload'].read()
    response_data = json.loads(response_data)
    if response_data['statusCode'] == 200:
        return response_data['body']
    else:
        raise Exception(response_data['body']['error'])

def get_site_category(site_id):
    payload = json.dumps({
            'domain': site_id,
    })
    response = lambda_client.invoke(FunctionName='ssp_website_get_site_data', Payload=payload)
    response = decode_stream(response)
    
    return response['site_category']
    
def start_auction(site_id, site_category, hour):
    payload = json.dumps({
            'site_id': site_id,
            'site_category': site_category,
            'hour': hour
    })
    response = lambda_client.invoke(FunctionName='adx_auction', Payload=payload)
    response = decode_stream(response)
    return response
        
def lambda_handler(event, context):
    try:
        # extract slot data
        site_id = event['site_id']
        hour = event['hour']
        site_category = get_site_category(site_id)
        
        # perform auction
        winner = start_auction(site_id, site_category, hour)

        statusCode = 200
        response_body = {
            'id_captcha': winner['id_captcha'],
            'stars' : winner['stars']
        }
        
    except Exception as err:
        statusCode = 500
        response_body = {'error': 'slot_handler: ' + str(err)}
       
    return {
            'statusCode' : statusCode,
            'body' : response_body
    }
    
    
