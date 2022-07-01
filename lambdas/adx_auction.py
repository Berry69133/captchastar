import json
import boto3
import asyncio

import time # per prove

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
        
# async wrapper for decode stream 
async def async_decode_stream(response_stream):
    return decode_stream(response_stream)

async def get_bids_async_wrapper(campaign_ids, slot_data):
    # create e payload data for each campaign
    payloads = []
    for id_campaign in campaign_ids: 
        p = json.dumps({
            'id_campaign': id_campaign,
            'slot_data' : slot_data
        })
        payloads.append(p)
        
    # invoke a 'dsp_bidding_get_bid' function for each payload previously created in parallel
    bids = await asyncio.gather(
        *[async_decode_stream(lambda_client.invoke(FunctionName='dsp_bidding_get_bid', Payload=p)) for p in payloads] 
    )
    return bids

# retrieve a list of ids of active campaings (from the db 'ad-exchange-cs')
# IMPORTANT: ad-exchange contains only one row: 
#   key: campaigns='active' ,
#   attributes: ids=[ids of active campaigns] 
def get_active_campaigns():
    table = dynamodb.Table('ad-exchange-cs')
    response = table.get_item(Key={'campaigns': 'active'})
    if 'Item' in response:
        ids = response['Item']['ids']
    else:
        ids = []
    return ids

def get_default_captcha():
    payload = json.dumps({})
    response_stream = lambda_client.invoke(FunctionName='captcha_get_default', Payload=payload)
    response = decode_stream(response_stream)
    return response['id_captcha'], response['stars']

async def log(auction_id, slot_data, bids_data, winner_index):
    campaigns_data = []
    for idx, campaign in enumerate(bids_data):
        win = (idx == winner_index)
        c = {
            'id_campaign': campaign['id_campaign'],
            'id_captcha': campaign['id_captcha'],
            'bid': campaign['bid'],
            'win': win
        }
        campaigns_data.append(c)
    
    payload = {
        'auction_id': auction_id,
        'site_id': slot_data['site_id'],
        'hour': slot_data['hour'],
        'weekday': slot_data['weekday'],
        'os': slot_data['os'],
        'browser': slot_data['browser'],
        'city': slot_data['city'],
        'region': slot_data['region'],
        'site_data': '0', # not used right now
        'campaigns': campaigns_data
    }
    
    p = json.dumps(payload)
    # no need to wait the completition of the logging
    decode_stream(lambda_client.invoke(FunctionName='log_append_log', Payload=p))

# retrieve capctha stars
def get_captcha_stars(id_captcha):
    try:
        payload = json.dumps({
            'id_captcha' : id_captcha
        })
        response = lambda_client.invoke(FunctionName='captcha_get_captcha', Payload=payload)
        response = decode_stream(response)
        return response['stars']
        
    except Exception as err:
        raise Exception('get_captcha_stars: ' + str(err))

# main
def lambda_handler(event, context):
    try:
        auction_id = context.aws_request_id
        slot_data = event['slot_data']
        
        # retrieve a list of ids of active campaings 
        campaign_ids = get_active_campaigns()
        
        # check if there is at least one active campaign
        if len(campaign_ids) > 0:
            # get data relative to the bid from each campaign
            bids_data = asyncio.run(get_bids_async_wrapper(campaign_ids, slot_data)) 
            
            # exclude dsps which bidded -1*CTR (i.e. any negative value) -> do not partecipate in the auction
            bids_data = [x for x in bids_data if x['bid'] > 0]
            
            # retrieve bids from every participant
            bid_values = [x['bid'] for x in bids_data]
            
            n_bids = len(bid_values)
            # check if there are participants
            if n_bids > 0:
                # retrieve the index of the max bid (with an argmax on the bid values)
                winner_index = max(range(n_bids), key=lambda i: bid_values[i])
                
                # retrieve data of the winner
                winner = bids_data[winner_index]
                winning_id_captcha = winner['id_captcha']
                winning_stars = get_captcha_stars(winning_id_captcha)
                
                # retrieve second price
                bid_values.sort(reverse=True)
                second_bid = bid_values[1] if n_bids>1 else winner['bid']
                
                log(auction_id, slot_data, bids_data, winner_index)
                
            # if there are no bids
            else:
                # return default captcha
                winning_id_captcha, winning_stars = get_default_captcha()
        # if there is no active campaign 
        else:
            # return default captcha
            winning_id_captcha, winning_stars = get_default_captcha()
        
        statusCode = 200
        response_body = {
            'auction_id': auction_id,
            'winner': {
                'id_captcha': winning_id_captcha,
                'stars': winning_stars
            }
        }
        
    except Exception as err:
        statusCode = 500
        response_body = {'error' : 'adx: ' + str(err)}
        
    return {
        'statusCode' : statusCode,
        'body' : response_body
    }