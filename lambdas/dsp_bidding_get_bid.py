import json
import asyncio
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

async def get_ctr(id_campaign, site_id, site_category, hour):
    try:
        payload = json.dumps({
            'ad_id': id_campaign,
            'site_id' : site_id,
            'site_category' : site_category,
            'hour' : hour
        })
        
        response = lambda_client.invoke(FunctionName='dsp_bidding_getCTR', Payload=payload)
        response = decode_stream(response)
        ctr = response['ctr']
        return ctr
        
    except Exception as err:
        raise Exception('get_ctr async call: ' + str(err))

async def get_bid_data(id_campaign):
    try:
        payload = json.dumps({
            'id_campaign': id_campaign
        })
        response = lambda_client.invoke(FunctionName='dsp_campaign_get_bid_data', Payload=payload)
        response = decode_stream(response)
        
        if response: #check if the response is not empty
            id_captcha = response['id_captcha']
            stars = response['stars']
            max_cpc = response['max_cpc']
            return max_cpc, id_captcha, stars
            
        # if for whatever reason, we didn't get the data back, we send -1 as max_cpc => do not partecipate in the auction
        else: 
            return -1, "", "" 
    except Exception as err:
        raise Exception('get_bid_data async call: ' + str(err))

# wrapper to call get_bid_data and get_CTR in parallel
async def async_wrapper(id_campaign, site_id, site_category, hour):
    try:
        data = await asyncio.gather(
            get_bid_data(id_campaign), 
            get_ctr(id_campaign, site_id, site_category, hour)
        )
        
        bid_data, ctr = data
        max_cpc, id_captcha, stars = bid_data
        return max_cpc, id_captcha, stars, ctr
        
    except Exception as err:
        raise Exception('error in async call: ' + str(err))

# main
def lambda_handler(event, context):
    try:
        id_campaign = event['id_campaign']
        site_id = event['site_id']
        site_category = event['site_category']
        hour = event['hour']
        
        # parallel calls to retrieve ctr and bid data
        max_cpc, id_captcha, stars, ctr = asyncio.run(async_wrapper(id_campaign, site_id, site_category, hour))

        statusCode = 200
        response_body = {
            'id_campaign': id_campaign,
            'id_captcha' : id_captcha,
            'stars': stars, 
            'bid': float(max_cpc)*float(ctr)
        }
        
    except Exception as err:
        statusCode = 500
        response_body = {'error': 'get_bid: ' + str(err)}
    
    return {
        'statusCode' : statusCode,
        'body' : response_body
    }
    
    
