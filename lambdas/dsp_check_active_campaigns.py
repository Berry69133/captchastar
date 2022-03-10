import json
import boto3

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# decode the lambda return 
async def decode_stream(response_stream):
    response_data = response_stream['Payload'].read()
    print(response_data)
    response_data = json.loads(response_data)
    if response_data['statusCode'] == 200:
        return response_data['body']
    else:
        raise Exception(response_data['body']['error'])

# main
def lambda_handler(event, context):
    time = event['time'] #2022-03-09T13:54:00Z
    date = time[0:10] #2022-03-09
    year, month, day = date.split("-") #2022, 03, 09
    
    #TODO: do stuff with date
    
    # get every campaign (lento?)
    table = dynamodb.Table('dsp-campaign-cs')
    campaigns = table.scan(AttributesToGet=['id_campaign', 'deleted'])['Items']
    
    # filter by non-deleted
    campaigns = [x['id_campaign'] for x in campaigns if not x['deleted']]
    #TODO: droppare le deleted dal nostro db dsp-campaign-cs
    
    # send updated list of active campaigns to adx
    payload =  json.dumps({'ids': campaigns})
    lambda_client.invoke(FunctionName='adx_update_active_campaigns', Payload=payload)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


