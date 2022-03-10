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

def put_captcha_in_db(table, id_advertiser, id_captcha, img_base64, stars, sol_x, sol_y):
    try:
        captcha_data = {
                'id_advertiser': id_advertiser,
                'id_captcha': id_captcha,
                'img_base64': img_base64,
                'stars': stars,
                'sol_x': sol_x,
                'sol_y': sol_y
        }
        table.put_item(Item=captcha_data)
    except Exception as err:
        raise Exception(err)

def lambda_handler(event, context):
    try:
        id_advertiser = event['id_advertiser']
        img_base64 = event['img_base64']
        captcha_name = event['captcha_name']
        
        table = dynamodb.Table('captcha-db-cs')
        
        new_id_captcha = captcha_name + "-" + id_advertiser
        
        # retrieve data from response: stars, sol_x, sol_y
        payload = json.dumps({'img_base64': img_base64})
        response = lambda_client.invoke(FunctionName='captcha_generate_captcha', Payload=payload)
        response = decode_stream(response)
        
        
        # add captcha in db
        put_captcha_in_db(table, id_advertiser, new_id_captcha, img_base64, response['stars'], response['sol_x'], response['sol_y'])
        
        statusCode = 200

    except Exception as err:
        statusCode = 500
        print(err)
        
    return {
        'statusCode' : statusCode
    }
   