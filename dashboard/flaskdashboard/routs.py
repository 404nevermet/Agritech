from fileinput import filename
from flaskdashboard import app 
from flask import render_template as renderer, url_for
import json
import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr


DYNAMODB_SPRINKLER_STATE_TABLE = "sprinkler_state_table"
DYNAMODB_AGGREGATE_DATA_TABLE ="aggregate_data_table"

colorArray = ['#FFC107', '#DC3545',"#0DCAF0","#198754", "#0D6EFD",
            '#FF6633', '#FFB399', '#FF33FF', '#FFFF99', '#00B3E6', 
		  '#E6B333', '#3366E6', '#999966', '#99FF99', '#B34D4D',
		  '#80B300', '#809900', '#E6B3B3', '#6680B3', '#66991A', 
		  '#FF99E6', '#CCFF1A', '#FF1A66', '#E6331A', '#33FFCC',
		  '#66994D', '#B366CC', '#4D8000', '#B33300', '#CC80CC', 
		  '#66664D', '#991AFF', '#E666FF', '#4DB3FF', '#1AB399',
		  '#E666B3', '#33991A', '#CC9999', '#B3B31A', '#00E680', 
		  '#4D8066', '#809980', '#E6FF80', '#1AFF33', '#999933',
		  '#FF3380', '#CCCC00', '#66E64D', '#4D80CC', '#9900B3', 
		  '#E64D66', '#4DB380', '#FF4D4D', '#99E6E6', '#6666FF']

class DynamoDBUtil:
    def __init__(self):
        self._dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
        self._table = None
    
    def get_table(self, table_name):
        return self._dynamodb.Table(table_name)

    def is_table_exits(self, table_name):
        table = self._dynamodb.Table(table_name)
        try:
            is_table_existing = table.table_status in ("CREATING", "UPDATING",
                                                       "DELETING", "ACTIVE")
        except ClientError:
            is_table_existing = False
            print("Table {} doesn't exist.".format(table.table_name))
        return is_table_existing

    def create_table_if_not_exist(self, table_name, partition_key='deviceId', partition_key_type='S', sort_key='timestamp', sort_key_type='S'):
        if self.is_table_exits(table_name):
            print('Table already exists')
        else:
            table = self._dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': partition_key,
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': sort_key,
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': partition_key,
                        'AttributeType': partition_key_type
                    },
                    {
                        'AttributeName': sort_key,
                        'AttributeType': sort_key_type
                    }
                ],

                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("Creating table...")
            table.meta.client.get_waiter(
                'table_exists').wait(TableName=table_name)
            print("Table {} created".format(table.table_name))

    def get_data(self, table_name):
        table = self.get_table(table_name)
        response = table.scan()
        data = response["Items"]
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response["Items"])
        return data

    def get_data_between_time_range(self, table_name, from_time, to_time):
        table = self.get_table(table_name)
        response = table.scan(FilterExpression=Attr(
            'timestamp').between(from_time, to_time))
        data = response["Items"]
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response["Items"])
        return data

    def bulk_insert(self, table_name, items):
        table = self.get_table(table_name)
        with table.batch_writer() as batch:
            for item in items:
                print(item)
                batch.put_item(Item=item)
    
    def update_entry(self, table_name, keyName, keyValue, updatKey, updateValue):
        table = self.get_table(table_name)
        updateExp = "set {} = :value".format(updatKey)
        update_status = table.update_item(
                Key={keyName: keyValue},
                UpdateExpression=updateExp,
                ExpressionAttributeValues={':value': updateValue},
                ReturnValues="UPDATED_NEW"
            )
        return update_status


def generate_graph_data(data):
    labels = [ entry['timestamp'] for entry in data  if entry['zoneId'] == data[0]['zoneId']]
    deviceWiseData = {}
    for entry in data:
        if not entry['zoneId'] in deviceWiseData.keys():
            deviceWiseData[entry['zoneId']] = []
        deviceWiseData[entry['zoneId']].append(entry['value'])
    
    print(labels)
    print(deviceWiseData)
    return (labels,deviceWiseData )

@app.route("/")
@app.route("/home")
def home():
    return renderer('home.html')

@app.route("/status")
def status():
    dbUtil =  DynamoDBUtil()
    sprinkler_states = dbUtil.get_data(DYNAMODB_SPRINKLER_STATE_TABLE)
    print(sprinkler_states)
    return renderer('status.html', sprinklers=sprinkler_states)


@app.route("/zonedata")
def zonedata():
    start_time = (datetime.now() - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

    
    dbUtil =  DynamoDBUtil()
    data = dbUtil.get_data_between_time_range(DYNAMODB_AGGREGATE_DATA_TABLE, start_time, end_time)
    print(data)
    graph_data = generate_graph_data(data)
    print(graph_data)
    return renderer('zonedata.html', labels=graph_data[0], values=graph_data[1], colors=colorArray)

"""

@app.route("/graph")
def graph():
    filename = os.path.join(app.static_folder, 'sampledata.json')
    with open(filename) as data_file:
        sampledata = json.load(data_file)
    labels = [ entry['timestamp'] for entry in sampledata]
    
    deviceWiseData = {}
    for entry in sampledata:
        if not entry['deviceId'] in deviceWiseData.keys():
            deviceWiseData[entry['deviceId']] = []
        deviceWiseData[entry['deviceId']].append(entry['value'])
    
    print(labels)
    print(deviceWiseData)

    return renderer('graph.html', labels=labels, values=deviceWiseData, colors=colorArray)


"""
