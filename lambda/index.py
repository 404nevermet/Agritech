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
#from test_sprinkler import DYNAMODB_SPRINKLER_STATE_TABLE

# Meta data that device sends during registration
DYNAMODB_DEVICE_METADATA_TABLE = 'device_meta_data_table'
# Computed zone-wise aggregated data
DYNAMODB_AGGREGATE_DATA_TABLE = 'aggregate_data_table'
# Alert situation data sent to sprinklers
DYNAMODB_SPRINKLER_ALERTS_TABLE = 'sprinkler_alerts_table'
# Sprinklers state management data
DYNAMODB_SPRINKLER_STATUS_TABLE = 'sprinkler_state_table'

THRESHOLD_LOW_HUMIDITY = 40.0
THRESHOLD_HIGH_HUMIDITY = 80.0
THRESHOLD_TEMP = 25.0

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
    #db_name = "agro_agg_data_table"
    db_name = DYNAMODB_AGGREGATE_DATA_TABLE
    DBName = db_name
    DBTable = None  # self._DBResource.Table(db_name)
    listResponse = DBClient.list_tables()
    tableList = listResponse['TableNames']
    print(tableList)
    if db_name in tableList:
        DBTable = DBResource.Table(db_name)
        print("Table already existing 2->", DBTable)
    else:
        #DBTable = "agro_agg_data_table"
        DBTable = DYNAMODB_AGGREGATE_DATA_TABLE
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
    #db_name = "sprinkler_status_on_events_table"
    db_name = DYNAMODB_SPRINKLER_ALERTS_TABLE
    DBName = db_name
    DBTable = None  # self._DBResource.Table(db_name)
    listResponse = DBClient.list_tables()
    tableList = listResponse['TableNames']
    print(tableList)
    if db_name in tableList:
        DBTable = DBResource.Table(db_name)
        print("Table already existing 2->", DBTable)
    else:
        #DBTable = "sprinkler_status_on_events_table"
        DBTable = DYNAMODB_SPRINKLER_ALERTS_TABLE
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
    #db_name = "sprinkler_zone_state_table"
    db_name = DYNAMODB_SPRINKLER_STATUS_TABLE
    DBName = db_name
    DBTable = None  # self._DBResource.Table(db_name)
    listResponse = DBClient.list_tables()
    tableList = listResponse['TableNames']
    print(tableList)
    if db_name in tableList:
        DBTable = DBResource.Table(db_name)
        print("Table already existing 2->", DBTable)
    else:
        #DBTable = "sprinkler_zone_state_table"
        DBTable = DYNAMODB_SPRINKLER_STATUS_TABLE
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
def get_aggeregate_data(aggregate_data):
    print("Arranging data for aggregation .....")
    values = {}
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

    for entry in aggregate_data:
        time_truncated_to_minutes = datetime.strptime(entry['timestamp'], '%Y-%m-%dT%H:%M:%SZ').strftime(
            '%Y-%m-%dT%H:%M:00Z')
        # if the value list does not exists for zone id create empty list
        if entry['zoneId'] not in values.keys():
            values[entry["zoneId"]] = {}

        # if dictionary for the devicetype does not exists then create an empty dictionary
        if entry['deviceType'] not in values[entry["zoneId"]].keys():
            values[entry["zoneId"]][entry['deviceType']] = {}

        # if dictionary for the datatype does not exists then create an empty dictionary
        if entry['datatype'] not in values[entry["zoneId"]][entry["deviceType"]].keys():
            values[entry["zoneId"]][entry['deviceType']][entry["datatype"]] = {}

        # if dictionary for the minute does not exists then create an empty dictionary and empty value list for the timestamp
        if time_truncated_to_minutes not in values[entry["zoneId"]][entry['deviceType']][entry['datatype']].keys():
            values[entry["zoneId"]][entry['deviceType']][entry['datatype']][time_truncated_to_minutes] = {}
            values[entry["zoneId"]][entry['deviceType']][entry['datatype']][time_truncated_to_minutes]["values"] = []

        values[entry["zoneId"]][entry['deviceType']][entry['datatype']][time_truncated_to_minutes]["values"].append(
            float(entry["value"]))

    print("values->", values)

    print("Aggregating data..")
    # print("input values->", values)
    aggregate_data = []
    # Calculate aggregate data
    # For each Zone Id Aggregate the data per DeviceType, DataType and TimeStamp
    # print("values.keys()->", values.keys())
    for device in values.keys():
        for devType in values[device].keys():
            # For each minute
            # For each datatype
            for datatype in values[device][devType].keys():
                # For each minute
                for timestamp in values[device][devType][datatype].keys():
                    values_list = values[device][devType][datatype][timestamp]["values"]
                    aggregate_data_entry = {}

                    aggregate_data_entry['zoneId'] = device
                    aggregate_data_entry['deviceType'] = devType
                    aggregate_data_entry['dataType'] = datatype
                    aggregate_data_entry['timestamp'] = timestamp
                    aggregate_data_entry['average'] = Decimal(str(round(sum(values_list) / len(values_list), 2)))
                    aggregate_data.append(aggregate_data_entry)
                    print("aggregate_data->", aggregate_data)
    return aggregate_data

def publishMQTTMessage(msgTopic, msgPayload):
    # a3pquorj9tve43-ats.iot.us-east-1.amazonaws.com
    client_iot = boto3.client('iot-data', region_name='us-east-1',
                              endpoint_url='https://a3pquorj9tve43-ats.iot.us-east-1.amazonaws.com')
    # Change topic, qos and payload
    print("Before Publishing")
    response = client_iot.publish(topic=msgTopic, qos=1, payload=msgPayload)
    time.sleep(5)
    print("After Publishing")

def lambda_handler(event, context):
    print("Start Lambda")
    # sns_client = boto3.client('sns')

    db_name = DYNAMODB_AGGREGATE_DATA_TABLE
    db_name1 = DYNAMODB_SPRINKLER_ALERTS_TABLE
    db_name2 = DYNAMODB_SPRINKLER_STATUS_TABLE
    table_name = DYNAMODB_DEVICE_METADATA_TABLE

    DBName = checkAndCreateAggrTable(DYNAMODB_AGGREGATE_DATA_TABLE)
    DBName = checkAndCreateSprinklerTable(DYNAMODB_SPRINKLER_ALERTS_TABLE)
    DBName = checkAndCreateSprinklerStateTable(DYNAMODB_SPRINKLER_STATUS_TABLE)
    data1 = get_data(DYNAMODB_DEVICE_METADATA_TABLE)

    data = []
    for record in event['Records']:
        payload = base64.b64decode(record["kinesis"]["data"])
        payload_str1 = str(payload)
        payload_str = json.loads(payload)
        print("Decoded Payload_str->", payload_str)
        deviceId = payload_str["deviceId"]
        deviceType = payload_str["deviceType"]
        datatype = payload_str["datatype"]
        value = payload_str["value"]
        timestamp = payload_str["timestamp"]
        data.append(json.loads(payload))
    data_with_zone = data

    # Append ZoneId, latitude,longitude to the Input Stream Data
    for datarec in data_with_zone:
        for datarec1 in data1:
            if (datarec['deviceId'] == datarec1['deviceId']):
                datarec.update(datarec1)
    ## Print the Appended Input STream Data with the ZoneId, latitude, longitude information.
    print("table_data_with_zone->", data_with_zone)
    # Aggregate the Data based on ZoneId, DeviceType, Datatype and Timestamp
    aggr_data = get_aggeregate_data(data_with_zone)
    print("Output Data is ->", aggr_data)

    #THRESHOLD_HUMIDITY = 5.0
    #THRESHOLD_TEMP = 24.0
    for record in aggr_data:
        newRecord = {
            "zoneId": {"S": str(record['zoneId'])},
            "deviceType": {"S": record['deviceType']},
            "dataType": {"S": record['dataType']},
            "timestamp": {"S": timestamp},
            "avgValue": {"S": str(record['average'])},
        }
        save_stat = insertIntoAggrDynamoTable(DYNAMODB_AGGREGATE_DATA_TABLE, newRecord)

        currdateandtime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        if (float(record['average']) < THRESHOLD_LOW_HUMIDITY):
            print("Soil Humidity is very Lower - ", record['average'], "% than the Threshold - ",
                  str(THRESHOLD_LOW_HUMIDITY), "%. Switch ON the Sprinkler in Zone - ", record['zoneId'])
            info_wthr = get_weather_info(lat, lon)
            if (float(info_wthr['celsius']) > THRESHOLD_TEMP):
                newRecord = {
                    "zoneId": {"S": str(record['zoneId'])},
                    "currdateandtime": {"S": currdateandtime},
                    "deviceType": {"S": record['deviceType']},
                    "dataType": {"S": record['dataType']},
                    "timestamp": {"S": timestamp},
                    "avgMoistureValue": {"S": str(record['average'])},
                    "avgTempValue": {"S": str(info_wthr['celsius'])},
                    "thresholdHumidity": {"S": str(THRESHOLD_LOW_HUMIDITY)},
                    "thresholdTemp": {"S": str(THRESHOLD_TEMP)},
                    "sprinklerStatus": {"S": "ON"}
                }
                save_stat = insertIntoSprinklerDynamoTable(DYNAMODB_SPRINKLER_ALERTS_TABLE, newRecord)
                # Update the STate of the Sprinkler by maintaining against the Zone. 1 Row per Zone
                return_stat = insertOrUpdateIntoSprinklerStateDynamoTable(DYNAMODB_SPRINKLER_STATUS_TABLE, str(record['zoneId']), "ON")
                return_item = get_data_with_key(DYNAMODB_SPRINKLER_STATUS_TABLE, str(record['zoneId']))
                if (return_item['State'] != "ON"):
                    mesgTopic = "actuator/command/set-state/" + str(record['zoneId'])
                    mesgPayload = json.dumps({"State": "ON"})
                    publishMQTTMessage(mesgTopic, mesgPayload)

        if (float(record['average']) > THRESHOLD_HIGH_HUMIDITY):
            print("Soil Humidity is Higher - ", record['average'], "% than the Threshold - ",
                  str(THRESHOLD_HIGH_HUMIDITY), "%. Switch OFF the Sprinkler in Zone - ", record['zoneId'])
            info_wthr = get_weather_info(lat, lon)
            if (float(info_wthr['celsius']) < THRESHOLD_TEMP):
                newRecord = {
                    "zoneId": {"S": str(record['zoneId'])},
                    "currdateandtime": {"S": currdateandtime},
                    "deviceType": {"S": record['deviceType']},
                    "dataType": {"S": record['dataType']},
                    "timestamp": {"S": timestamp},
                    "avgMoistureValue": {"S": str(record['average'])},
                    "avgTempValue": {"S": str(info_wthr['celsius'])},
                    "thresholdHumidity": {"S": str(THRESHOLD_HIGH_HUMIDITY)},
                    "thresholdTemp": {"S": str(THRESHOLD_TEMP)},
                    "sprinklerStatus": {"S": "OFF"}
                }
                save_stat = insertIntoSprinklerDynamoTable(DYNAMODB_SPRINKLER_ALERTS_TABLE, newRecord)
                # Update the STate of the Sprinkler by maintaining against the Zone. 1 Row per Zone
                return_stat = insertOrUpdateIntoSprinklerStateDynamoTable(DYNAMODB_SPRINKLER_STATUS_TABLE, str(record['zoneId']), "OFF")
                return_item = get_data_with_key(DYNAMODB_SPRINKLER_STATUS_TABLE, str(record['zoneId']))
                if (return_item['State'] != "OFF"):
                    mesgTopic = "actuator/command/set-state/" + str(record['zoneId'])
                    mesgPayload = json.dumps({"State": "OFF"})
                    publishMQTTMessage(mesgTopic, mesgPayload)

    print("End Lambda")