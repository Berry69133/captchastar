import json
import boto3

dynamodb = boto3.resource('dynamodb')
TOLERANCE = 42

def lambda_handler(event, context):
    try:
        id_captcha = event['id_captcha']
        mysol_x = int(event['mysol_x'])
        mysol_y = int(event['mysol_y'])
        
        # retrieve c data
        table = dynamodb.Table('captcha-db-cs')
        search_key = {
            'id_captcha': id_captcha
        }
        record = table.get_item(Key=search_key)
        
        # check if there is any result
        if not 'Item' in record.keys():
            raise Exception('no captcha found')
        else:
            captcha = record['Item']
            
            # retrieve original image to show in case of success
            img_base64 = captcha['img_base64']
            
            # extract captcha solution
            sol_x = captcha['sol_x']
            sol_y = captcha['sol_y']

            # check if solution is acceptable
            dist = (mysol_x-sol_x)*(mysol_x-sol_x)+(mysol_y-sol_y)*(mysol_y-sol_y)
            success = dist < TOLERANCE
            
            statusCode = 200
            response_body = {
                'success': success,
                'img_base64': img_base64 if success else ""   # return the original image iff the solution was acceptable
            }
            
    except Exception as err:
        print('check_solution ' + str(err))
        statusCode = 500
        response_body = {
                'success': False,
                'img_base64': ""
        }
    
    return {
        'statusCode': 200,
        'body': response_body
    }
