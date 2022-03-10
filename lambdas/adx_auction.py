import json
import boto3
import asyncio

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# decode the lambda return 
async def decode_stream(response_stream):
    response_data = response_stream['Payload'].read()
    response_data = json.loads(response_data)
    if response_data['statusCode'] == 200:
        return response_data['body']
    else:
        raise Exception(response_data['body']['error'])

async def get_bids_async_wrapper(campaign_ids, site_id, site_category, hour):
    # create e payload data for each campaign
    payloads = []
    for id_campaign in campaign_ids: 
        p = json.dumps({
                'id_campaign': id_campaign,
                'site_id' : site_id,
                'site_category' : site_category,
                'hour' : hour
        })
        payloads.append(p)
        
    # invoke a 'dsp_bidding_get_bid' function for each payload previously created in parallel
    bids = await asyncio.gather(
        *[decode_stream(lambda_client.invoke(FunctionName='dsp_bidding_get_bid', Payload=p)) for p in payloads] 
    )
    
    return bids

# retrieve a list of ids of active campaings (from the db 'ad-exchange-cs')
# IMPORTANT: ad-exchange contains only one row: 
#   key: campaigns='active' ,
#   attributes: ids=[ids of active campaigns] 
def get_active_campaigns():
    table = dynamodb.Table('ad-exchange-cs')
    response = table.get_item(Key={'campaigns': 'active'})
    response = response['Item']
    return response['ids']

def get_default_captcha():
    payload = json.dumps()
    response_stream = lambda_client.invoke(FunctionName='captcha_get_default', Payload=payload)
    response = decode_stream(response_stream)
    return response

def lambda_handler(event, context):
    try:
        site_id = event['site_id']
        site_category = event['site_category']
        hour = event['hour']
        
        # retrieve a list of ids of active campaings 
        campaign_ids = get_active_campaigns()
        
        # check if there is at least one active campaign
        if len(campaign_ids) > 0:
            # get bids from each campaign
            bids_data = asyncio.run(get_bids_async_wrapper(campaign_ids, site_id, site_category, hour)) 
            
            # exclude dsps which bidded -1*CTR (i.e. any negative value) => do not partecipate in the auction
            bids_data = [x for x in bids_data if x['bid'] > 0]
            
            # retrieve bids from every participant
            bid_values = [x['bid'] for x in bids_data]
            
            # check if there are  participants
            n_bids = len(bid_values)
            if n_bids > 1:
                # retrieve the index of the max bid (with an argmax on the bid values)
                winner_index = max(range(n_bids), key=lambda i: bid_values[i])
                winner = bids_data[winner_index]
                # retrieve second price
                bid_values.sort(reverse=True)
                second_bid = bid_values[1]
            elif n_bids == 1:
                # set winner and winning bid to the values of the only participant
                winner = bids_data[0]
                second_bid = winner['bid']
            # case when there are no bids
            else:
                # return default captcha
                winner = get_default_captcha()
        # case when there is no active campaign 
        else:
            # return default captcha
            winner = get_default_captcha()
        
        statusCode = 200
        response_body = {
            'id_captcha': winner['id_captcha'],
            'stars': winner['stars'],
        }
        
    except Exception as err:
        statusCode = 500
        response_body = {'error' : 'adx: ' + str(err)}
        
    return {
        'statusCode' : statusCode,
        'body' : response_body
    }