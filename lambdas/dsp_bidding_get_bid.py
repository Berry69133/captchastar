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

def get_ctr(id_advertiser, slot_data):
    try:
        payload = json.dumps({
            'slot_data': slot_data,
            'id_advertiser': id_advertiser
        })
        response = lambda_client.invoke(FunctionName='dsp_bidding_getCTR', Payload=payload)
        response = decode_stream(response)
        ctr = response['ctr']
        return ctr
        
    except Exception as err:
        raise Exception('get_ctr: ' + str(err))

def get_bid_data(id_campaign):
    try:
        payload = json.dumps({
            'id_campaign': id_campaign
        })
        response = lambda_client.invoke(FunctionName='dsp_campaign_get_bid_data', Payload=payload)
        response = decode_stream(response)
        
        if response: #check if the response is not empty
            id_captcha = response['id_captcha']
            ecpc = response['ecpc']
            id_advertiser = response['id_advertiser']
            return ecpc, id_captcha, id_advertiser
            
        # if for whatever reason, we didn't get the data back, we send -1 as max_cpc => do not partecipate in the auction
        else: 
            return -1, "", "", -1
    except Exception as err:
        raise Exception('get_bid_data: ' + str(err))

# main
def lambda_handler(event, context):
    try:
        slot_data = event['slot_data']
        id_campaign = event['id_campaign']
        
        ecpc, id_captcha, id_advertiser = get_bid_data(id_campaign)
        ctr = get_ctr(id_advertiser, slot_data)
        
        # bid = eCPC * eCTR
        bid = float(ecpc)*float(ctr)

        statusCode = 200
        response_body = {
            'id_campaign': id_campaign,
            'id_captcha' : id_captcha,
            'bid': bid
        }
        
    except Exception as err:
        statusCode = 500
        response_body = {'error': 'get_bid: ' + str(err)}
    
    return {
        'statusCode' : statusCode,
        'body' : response_body
    }