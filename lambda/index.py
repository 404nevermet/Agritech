from __future__ import print_function
import json
import base64
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import requests
import time
from botocore.exceptions import ClientError

from test_sprinkler import DYNAMODB_SPRINKLER_STATE_TABLE


# Meta data that device sends during registration
DYNAMODB_DEVICE_METADATA_TABLE = 'device_metadata_table'
# Computed zone-wise aggregated data
DYNAMODB_AGGREGATE_DATA_TABLE = 'aggregate_data_table'
# Alert situation data sent to sprinklers
DYNAMODB_SPRINKLER_ALERTS_TABLE = 'sprinkler_alerts_table'
# Sprinklers state management data
DYNAMODB_SPRINKLER_STATUS_TABLE = 'sprinkler_state_table'

THRESHOLD_LOW_HUMIDITY = 40.0
THRESHOLD_HIGH_HUMIDITY = 80.0
THRESHOLD_TEMP = 15.0

DBClient = boto3.client("dynamodb", region_name="us-east-1")
DBResource = boto3.resource("dynamodb", region_name="us-east-1")

url = "https://api.openweathermap.org/data/2.5/weather"
api_key = "e83b3c4c08285bf87b99f9bbc0abe3f0"
lat = 25.774
lon = -80.1937

def get_aws_iot_ats_endpoint():
    """
    Get the "Data-ATS" endpoint instead of the
    untrusted "Symantec" endpoint that's built-in.
    """
    iot_client = boto3.client(
        "iot",
        #aws_access_key_id=AWS_ACCESS_KEY_ID,
        #aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        #region_name= REGION_NAME,
        verify=True
    )
    details = iot_client.describe_endpoint(endpointType="iot:Data-ATS")
    host = details.get("endpointAddress")
    return f"https://{host}"

def get_weather_info(lat_value, lon_value):
    response = requests.get(url, params={'lat': lat_value, 'lon': lon_value, 'units': 'metric', 'appid': api_key})
    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print("Invalid lat long")

    degree = data.get('main').get('temp')
    weather = data.get('weather')[0].get('main')
    weather_info = {'lat': lat_value, 'lon': lon_value, 'weather': weather, 'celsius': degree}
    print(weather_info)
    return weather_info

def insertIntoAggrDynamoTable(db_name, newRecord):
    try:
        logger = logging.getLogger('boto3.dynamodb.table')
        logger.setLevel(logging.DEBUG)
        save_status = DBClient.put_item(TableName=db_name, Item=newRecord)
        return save_status
    except ClientError as e:
        # This error never happens.
        print("ERROR")
        print(e.response["Error"]['Message'])

def insertIntoSprinklerDynamoTable(db_name, newRecord):
    try:
        logger = logging.getLogger('boto3.dynamodb.table')
        logger.setLevel(logging.DEBUG)
        save_status = DBClient.put_item(TableName=db_name, Item=newRecord)
        time.sleep(1)
        return save_status
    except ClientError as e:
        # This error never happens.
        print("ERROR")
        print(e.response["Error"]['Message'])

def checkAndCreateAggrTable(db_name):
    db_name = "agro_agg_data_table"
    DBName = db_name
    DBTable = None  # self._DBResource.Table(db_name)
    listResponse = DBClient.list_tables()
    tableList = listResponse['TableNames']
    print(tableList)
    if db_name in tableList:
        DBTable = DBResource.Table(db_name)
        print("Table already existing 2->", DBTable)
    else:
        DBTable = "agro_agg_data_table"
        print("Table does not exist. Creation in Progress->", DBTable)
        # DBTable = None
        aggrAttrDef = [
            {"AttributeName": "zoneId", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"}
        ]
        aggrKeySchema = [
            {"AttributeName": "zoneId", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"}
        ]
        aggrProvisionedThroughput = {
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5
        }
        DBTable = DBResource.create_table(TableName=db_name,
                                          AttributeDefinitions=aggrAttrDef,
                                          KeySchema=aggrKeySchema,
                                          ProvisionedThroughput=aggrProvisionedThroughput)
        DBTable.wait_until_exists()
        # return DBTable, DBClient, DBResource, DBName
        return DBName

def checkAndCreateSprinklerTable(db_name):
    db_name = "sprinkler_status_on_events_table"
    DBName = db_name
    DBTable = None  # self._DBResource.Table(db_name)
    listResponse = DBClient.list_tables()
    tableList = listResponse['TableNames']
    print(tableList)
    if db_name in tableList:
        DBTable = DBResource.Table(db_name)
        print("Table already existing 2->", DBTable)
    else:
        DBTable = "sprinkler_status_on_events_table"
        print("Table does not exist. Creation in progress->", DBTable)
        # DBTable = None
        aggrAttrDef = [
            {"AttributeName": "zoneId", "AttributeType": "S"},
            {"AttributeName": "currdateandtime", "AttributeType": "S"}
        ]
        aggrKeySchema = [
            {"AttributeName": "zoneId", "KeyType": "HASH"},
            {"AttributeName": "currdateandtime", "KeyType": "RANGE"}
        ]
        aggrProvisionedThroughput = {
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5
        }
        DBTable = DBResource.create_table(TableName=db_name,
                                          AttributeDefinitions=aggrAttrDef,
                                          KeySchema=aggrKeySchema,
                                          ProvisionedThroughput=aggrProvisionedThroughput)
        DBTable.wait_until_exists()
        # return DBTable, DBClient, DBResource, DBName
        return DBName

def checkAndCreateSprinklerStateTable(db_name):
    db_name = "sprinkler_zone_state_table"
    DBName = db_name
    DBTable = None  # self._DBResource.Table(db_name)
    listResponse = DBClient.list_tables()
    tableList = listResponse['TableNames']
    print(tableList)
    if db_name in tableList:
        DBTable = DBResource.Table(db_name)
        print("Table already existing 2->", DBTable)
    else:
        DBTable = "sprinkler_zone_state_table"
        print("Table does not exist. Creation in Progress->", DBTable)
        # DBTable = None
        aggrAttrDef = [
            {"AttributeName": "zoneId", "AttributeType": "S"},
        ]
        aggrKeySchema = [
            {"AttributeName": "zoneId", "KeyType": "HASH"}
        ]
        aggrProvisionedThroughput = {
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5
        }
        DBTable = DBResource.create_table(TableName=db_name,
                                          AttributeDefinitions=aggrAttrDef,
                                          KeySchema=aggrKeySchema,
                                          ProvisionedThroughput=aggrProvisionedThroughput)
        DBTable.wait_until_exists()
        # return DBTable, DBClient, DBResource, DBName
        return DBName

def insertOrUpdateIntoSprinklerStateDynamoTable(db_name, tabKey, updValue):
    try:
        logger = logging.getLogger('boto3.dynamodb.table')
        logger.setLevel(logging.DEBUG)
        table = DBResource.Table(db_name)
        if (table.item_count == 0):
            newRecord = {
                "zoneId": {"S": tabKey},
                "State": {"S": updValue}
            }
            save_status = DBClient.put_item(TableName=db_name, Item=newRecord)
            time.sleep(1)
            return save_status
        else:
            upd_status = table.update_item(
                Key={'zoneId': tabKey},
                UpdateExpression="set State = :stateInfo",
                ExpressionAttributeValues={':stateInfo': updValue},
                ReturnValues="UPDATED_NEW"
            )
            time.sleep(1)
            return upd_status

    except ClientError as e:
        # This error never happens.
        print("ERROR")
        print(e.response["Error"]['Message'])

def get_data_with_key(table_name, key_name):
    table = DBResource.Table(table_name)
    try:
        response = table.get_item(Key={'zoneId': key_name})
    except ClientError as e:
        print("ERROR")
        print(e.response["Error"]['Message'])
    else:
        return response['Item']

def get_data(table_name):
    table = DBResource.Table(table_name)
    response = table.scan()
    data = response["Items"]
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response["Items"])
    return data

# Arranges data into sorted order for aggregate data generation
def get_aggeregate_data(telemetry_data):
    structured_data = create_structured_telemetry_data(telemetry_data)
    print("Aggregating data..")
    aggregate_data = []
    # Calculate aggregate data
    # For each Zone Id Aggregate the data per DeviceType, DataType and TimeStamp
    for device in structured_data.keys():
        for devType in structured_data[device].keys():
            # For each minute
            # For each datatype
            for datatype in structured_data[device][devType].keys():
                # For each minute
                for timestamp in structured_data[device][devType][datatype].keys():
                    values_list = structured_data[device][devType][datatype][timestamp]["values"]
                    aggregate_data_entry = {}

                    aggregate_data_entry['zoneId'] = device
                    aggregate_data_entry['deviceType'] = devType
                    aggregate_data_entry['dataType'] = datatype
                    aggregate_data_entry['timestamp'] = timestamp
                    aggregate_data_entry['average'] = Decimal(str(round(sum(values_list) / len(values_list), 2)))
                    aggregate_data.append(aggregate_data_entry)

    return aggregate_data

def create_structured_telemetry_data(telemetry_data):
    structured_data = {}
    # Sample of aggregated values
    # ===============================
    # {
    #    "Zone":{
    #       "deviceType":{
    #            "datatype":{
    #          "2021-09-26T01:37:00Z":{
    #                 "values":[
    #                       82.0,
    #                       95.0
    #                   ]
    #                },
    #            },
    #       },
    #    },
    # }

    for entry in telemetry_data:
        time_truncated_to_minutes = datetime.strptime(entry['timestamp'], '%Y-%m-%dT%H:%M:%SZ').strftime(
            '%Y-%m-%dT%H:%M:00Z')
        # if the value list does not exists for zone id create empty list
        if entry['zoneId'] not in structured_data.keys():
            structured_data[entry["zoneId"]] = {}

        # if dictionary for the devicetype does not exists then create an empty dictionary
        if entry['deviceType'] not in structured_data[entry["zoneId"]].keys():
            structured_data[entry["zoneId"]][entry['deviceType']] = {}

        # if dictionary for the datatype does not exists then create an empty dictionary
        if entry['datatype'] not in structured_data[entry["zoneId"]][entry["deviceType"]].keys():
            structured_data[entry["zoneId"]][entry['deviceType']][entry["datatype"]] = {}

        # if dictionary for the minute does not exists then create an empty dictionary and empty value list for the timestamp
        if time_truncated_to_minutes not in structured_data[entry["zoneId"]][entry['deviceType']][entry['datatype']].keys():
            structured_data[entry["zoneId"]][entry['deviceType']][entry['datatype']][time_truncated_to_minutes] = {}
            structured_data[entry["zoneId"]][entry['deviceType']][entry['datatype']][time_truncated_to_minutes]["values"] = []

        structured_data[entry["zoneId"]][entry['deviceType']][entry['datatype']][time_truncated_to_minutes]["values"].append(
            float(entry["value"]))

    print("values->", structured_data)
    return structured_data

def publishMQTTMessage(msgTopic, msgPayload):
    # a3pquorj9tve43-ats.iot.us-east-1.amazonaws.com
    client_iot = boto3.client('iot-data', region_name='us-east-1',
                              endpoint_url='https://a3pquorj9tve43-ats.iot.us-east-1.amazonaws.com')
    # Change topic, qos and payload
    print("Before Publishing")
    response = client_iot.publish(topic=msgTopic, qos=1, payload=msgPayload)
    time.sleep(10)
    print("After Publishing")


def create_device_metadata_map(raw_meta_data):
    # Format
    # {
    #   "SoilSensor" :{
    #       "SMS-001" :  {"deviceId":"SMS-001", "deviceType":"<>"...},
    #       "SMS-002" :  {"deviceId":"SMS-002", "deviceType":"<>"...}
    #        {
    #   },
    #   "Sprinkler": {
    #   }
    # }
    device_meta_data = {}
    for m_data in raw_meta_data:
        deviceType = m_data['deviceType']
        deviceId = m_data['deviceId']
        # For every new devie type add empty dictionary
        if not deviceType in device_meta_data.keys():
            device_meta_data[deviceType] = {}

        if not deviceId in device_meta_data[deviceType].keys():
            device_meta_data[deviceType][deviceId] = m_data

    return device_meta_data

def lambda_handler(event, context):

    checkAndCreateAggrTable(DYNAMODB_AGGREGATE_DATA_TABLE)
    checkAndCreateSprinklerTable(DYNAMODB_SPRINKLER_ALERTS_TABLE)
    checkAndCreateSprinklerStateTable(DYNAMODB_SPRINKLER_STATUS_TABLE)

    #Extract device metadata and create a dictinary for easy lookup
    device_metadata = get_data(DYNAMODB_DEVICE_METADATA_TABLE)
    device_metadata_map = create_device_metadata_map(device_metadata)


    # Get dta from event and append zone info from metadata table
    data_from_event = []
    for record in event['Records']:
        payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
        data_entry = json.loads(payload)

        deviceType = data_entry['deviceType']
        deviceId = data_entry['deviceId']
        sensor_metadata = device_metadata_map[deviceType]

        data_entry['zoneId'] = sensor_metadata[deviceId]['zoneId']
        data_entry['lattitude'] = sensor_metadata[deviceId]['lattitude']
        data_entry['longitude'] = sensor_metadata[deviceId]['longitude']
        data_from_event.append(json.loads(payload))

    # Aggregate the Data based on ZoneId, DeviceType, Datatype and Timestamp
    aggregated_data = get_aggeregate_data(data_from_event)

    THRESHOLD_TEMP = 15.0
    for record in aggregated_data:
        newRecord = {
            "zoneId": {"S": str(record['zoneId'])},
            "deviceType": {"S": record['deviceType']},
            "dataType": {"S": record['dataType']},
            "timestamp": {"S": record['timestamp']},
            "avgValue": {"S": str(record['average'])},
        }
        insertIntoAggrDynamoTable(DYNAMODB_AGGREGATE_DATA_TABLE, newRecord)

        currdateandtime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        if (float(record['average']) < THRESHOLD_LOW_HUMIDITY):
            print("Soil Humidity is very Lower - ", record['average'], "% than the Threshold - ",
                  str(THRESHOLD_LOW_HUMIDITY), "%. Switch ON the Sprinkler in Zone - ", record['zoneId'])
            weather_data = get_weather_info(lat, lon)
            if (float(weather_data['celsius']) > THRESHOLD_TEMP):
                newRecord = {
                    "zoneId": {"S": str(record['zoneId'])},
                    "currdateandtime": {"S": currdateandtime},
                    "deviceType": {"S": record['deviceType']},
                    "dataType": {"S": record['dataType']},
                    "timestamp": {"S": record['timestamp']},
                    "avgMoistureValue": {"S": str(record['average'])},
                    "avgTempValue": {"S": str(weather_data['celsius'])},
                    "thresholdHumidity": {"S": str(THRESHOLD_LOW_HUMIDITY)},
                    "thresholdTemp": {"S": str(THRESHOLD_TEMP)},
                    "sprinklerStatus": {"S": "ON"}
                }
                insertIntoSprinklerDynamoTable(DYNAMODB_SPRINKLER_ALERTS_TABLE, newRecord)
                # Update the STate of the Sprinkler by maintaining against the Zone. 1 Row per Zone
                insertOrUpdateIntoSprinklerStateDynamoTable(DYNAMODB_SPRINKLER_STATUS_TABLE, str(record['zoneId']), "ON")
                return_item = get_data_with_key(DYNAMODB_SPRINKLER_STATUS_TABLE, str(record['zoneId']))
                if (return_item['State'] != "ON"):
                    mesgTopic = "actuator/command/set-state/" + str(record['zoneId'])
                    mesgPayload = json.dumps({"State": "ON"})
                    publishMQTTMessage(mesgTopic, mesgPayload)

        if (float(record['average']) > THRESHOLD_HIGH_HUMIDITY):
            print("Soil Humidity is Higher - ", record['average'], "% than the Threshold - ",
                  str(THRESHOLD_HIGH_HUMIDITY), "%. Switch OFF the Sprinkler in Zone - ", record['zoneId'])
            weather_data = get_weather_info(lat, lon)
            if (float(weather_data['celsius']) < THRESHOLD_TEMP):
                newRecord = {
                    "zoneId": {"S": str(record['zoneId'])},
                    "currdateandtime": {"S": currdateandtime},
                    "deviceType": {"S": record['deviceType']},
                    "dataType": {"S": record['dataType']},
                    "timestamp": {"S": record['timestamp']},
                    "avgMoistureValue": {"S": str(record['average'])},
                    "avgTempValue": {"S": str(weather_data['celsius'])},
                    "thresholdHumidity": {"S": str(THRESHOLD_HIGH_HUMIDITY)},
                    "thresholdTemp": {"S": str(THRESHOLD_TEMP)},
                    "sprinklerStatus": {"S": "OFF"}
                }
                insertIntoSprinklerDynamoTable(DYNAMODB_SPRINKLER_ALERTS_TABLE, newRecord)
                # Update the State of the Sprinkler by maintaining against the Zone. 1 Row per Zone
                insertOrUpdateIntoSprinklerStateDynamoTable(DYNAMODB_SPRINKLER_STATUS_TABLE, str(record['zoneId']), "ON")
                return_item = get_data_with_key(DYNAMODB_SPRINKLER_STATUS_TABLE, str(record['zoneId']))
                if (return_item['State'] != "OFF"):
                    mesgTopic = "actuator/command/set-state/" + str(record['zoneId'])
                    mesgPayload = json.dumps({"State": "OFF"})
                    publishMQTTMessage(mesgTopic, mesgPayload)

    print("End Lambda")