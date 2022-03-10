import json
import boto3

dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')

POOL_ID = 'eu-central-1_1Ie1X6C6O'

def lambda_handler(event, context):
    try:
        id_publisher = event['id_publisher']
        domain = event['domain']
        site_category = event['site_category']
        
        # get list of publishers
        response = cognito.list_users(UserPoolId=POOL_ID)
        emails = [x['Attributes'][2]['Value'] for x in response['Users']]
        
        # check if the id_publisher exists
        if not id_publisher in emails:
            raise Exception('publisher not found')
        
        # add website
        table = dynamodb.Table('ssp-website-cs')
        new_website_data = {
            'domain': domain,
            'site_category': site_category,
            'id_publisher': id_publisher
        }
        table.put_item(Item=new_website_data)
        
        statusCode = 200
        response_body = {'success': True}
        
    except Exception as err:
        statusCode = 500
        response_body = {'success': False, 'error': str(err)}
    
    return {
        'statusCode': statusCode,
        'body': response_body
    }
