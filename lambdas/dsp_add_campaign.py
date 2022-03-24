import json
import boto3

dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')

POOL_ID = 'eu-central-1_ntP2CByxd'

def lambda_handler(event, context):
    try:
        id_advertiser = event['id_advertiser']
        id_captcha = event['id_captcha']
        campaign_name = event['campaign_name']
        budget = event['budget']
        ecpc = 1 # initialized as a constant, will be updated once we have data about the campaign

        # check if the id_advertiser exists
        response = cognito.list_users(UserPoolId=POOL_ID)
        emails = [x['Attributes'][2]['Value'] for x in response['Users']] # get list of advertiser ids
        if not id_advertiser in emails:
            raise Exception('advertiser not found')
        
        # generate unique id
        id_campaign = campaign_name + "-" + id_advertiser
        
        # add campaign
        table = dynamodb.Table('dsp-campaign-cs')
        new_campaign_data = {
            'id_advertiser': id_advertiser,
            'id_campaign': id_campaign,
            'ecpc': ecpc,
            'id_captcha': id_captcha,
            'budget': budget,
            'deleted': False
        }
        table.put_item(Item=new_campaign_data)
        
        statusCode = 200
        response_body = {'success': True}
        
    except Exception as err:
        statusCode = 500
        response_body = {'success': False, 'error': str(err)}
    
    return {
        'statusCode': statusCode,
        'body': response_body
    }
