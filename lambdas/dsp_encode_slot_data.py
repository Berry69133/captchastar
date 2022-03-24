import json
import random

def lambda_handler(event, context):
    try:
        id_advertiser = event['id_advertiser'] # used only because we are return random values in advertiser range, should be remove in the future
        # slot_data = event['slot_data'] # unused, right now we return random number
        res = {}
        
        # retrieve encoding for the advertiser
        fp = open('encoding.json')
        encodings = json.load(fp)
        advertiser_enc = encodings[id_advertiser]
        
        # return random numbers in range for each feature
        for feat in advertiser_enc.keys():
            n_vals = int(advertiser_enc[feat])
            encoded_feat = [0] * n_vals
            rand_idx = random.randint(0, n_vals-1)
            encoded_feat[rand_idx] = 1
            res[feat] = encoded_feat
            
        statusCode = 200
        response_body = {'encoded_features': res}
        
    except Exception as err:
        statusCode = 500
        response_body = {'success': False, 'error': 'encode slot data: ' + str(err)}
        
    return {
        'statusCode': statusCode,
        'body': response_body
    }
