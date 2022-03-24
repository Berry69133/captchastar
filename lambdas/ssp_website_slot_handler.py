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

def get_site_data(site_id):
    payload = json.dumps({
            'domain': site_id,
    })
    response = lambda_client.invoke(FunctionName='ssp_website_get_site_data', Payload=payload)
    response = decode_stream(response)
    
    # to update once we have more data about the website
    site_data = response['site_category']
    
    return site_data
    
def start_auction(slot_data):
    payload = json.dumps({
            'slot_data': slot_data
    })
    response = lambda_client.invoke(FunctionName='adx_auction', Payload=payload)
    response = decode_stream(response)
    return response
        
def lambda_handler(event, context):
    try:
        # extract slot data
        site_data = get_site_data(event['site_id'])
        slot_data = {
            'site_id': event['site_id'],
            'hour': event['hour'],
            'weekday': event['weekday'],
            'os': event['os'],
            'browser': event['browser'],
            'region': event['region'],
            'city': event['city'],
            'site_data': site_data
        }
        
        # perform auction
        winner = start_auction(slot_data)

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