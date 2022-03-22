from __future__ import print_function
import json
import base64
import boto3
from botocore.exceptions import ClientError
import logging
from boto3.dynamodb.conditions import Key, Attr
#import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal

DBClient = boto3.client("dynamodb", region_name="us-east-1")
DBResource = boto3.resource("dynamodb", region_name="us-east-1")

def insertIntoAggrDynamoTable(db_name, newRecord):
    try:
        # print("calling put_item")
        #print("newRecord->", newRecord)
        logger = logging.getLogger('boto3.dynamodb.table')
        logger.setLevel(logging.DEBUG)

        save_status = DBClient.put_item(TableName=db_name, Item=newRecord)
        #print(save_status)
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
        print("Table does not exist. Please create.->", DBTable)
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
        print ("After Table Creation")
        #return DBTable, DBClient, DBResource, DBName
        return DBName

def get_data(table_name):
    table = DBResource.Table(table_name)
    #table = get_table(table_name)
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
    #{
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
    #}

    for entry in aggregate_data:
        time_truncated_to_minutes = datetime.strptime(entry['timestamp'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%dT%H:%M:00Z')
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

        values[entry["zoneId"]][entry['deviceType']][entry['datatype']][time_truncated_to_minutes]["values"].append(float(entry["value"]))

    print ("values->", values)

    print("Aggregating data..")
    #print("input values->", values)
    aggregate_data = []
    # Calculate aggregate data
    # For each Zone Id Aggregate the data per DeviceType, DataType and TimeStamp
    #print("values.keys()->", values.keys())
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
                    #aggregate_data_entry['minimum'] = Decimal(str(min(values_list)))
                    #aggregate_data_entry['maximum'] = Decimal(str(max(values_list)))
                    aggregate_data_entry['average'] = Decimal(str(round(sum(values_list) / len(values_list), 2)))

                    aggregate_data.append(aggregate_data_entry)
                    print("aggregate_data->", aggregate_data)

    return aggregate_data


def lambda_handler (event, context):
    print("Start Lambda")
    #sns_client = boto3.client('sns')
    db_name = "agro_agg_data_table"
    DBName = checkAndCreateAggrTable(db_name)

    table_name = "device_meta_data_table"
    data1 = get_data(table_name)
    print ("data1", data1)
    #data1_df = pd.read_json(data1)

    print ("Before the Loop!!!")
    #print ("event->", event)
    print ("event['Records']", event['Records'])
    data = []
    for record in event['Records']:
        #print ("record->", record)
        payload = base64.b64decode(record["kinesis"]["data"])
        #print ("Decoded Payload->" + str(payload))
        payload_str1 = str(payload)
        payload_str = json.loads(payload)
        print("Decoded Payload_str->", payload_str)

        #payad_str_df = pd.read_json(payload_str)

        deviceId = payload_str["deviceId"]
        deviceType = payload_str["deviceType"]
        datatype = payload_str["datatype"]
        value = payload_str["value"]
        timestamp = payload_str["timestamp"]

        # print("DeviceId:", deviceId)
        # print("DeviceType:", deviceType)
        # print("DataType:", datatype)
        # print("Value:", value)
        # print("Timestamp:", timestamp)
        #print("DeviceZone:", devicezone)

        data.append(json.loads(payload))

    print ("Input Data is ->", data)
    data_with_zone = data

    # Append ZoneId, latitude,longitude to the Input Stream Data
    for datarec in data_with_zone:
        for datarec1 in data1:
            if (datarec['deviceId'] == datarec1['deviceId']):
                #print ("Zone Id is ->", datarec1['zoneId'])
                #print("Latitude is ->", datarec1['latitude'])
                #print("Longitude is ->", datarec1['longitude'])
                datarec.update(datarec1)
    ## Print the Appended Input STream Data with the ZoneId, latitude, longitude information.
    print ("table_data_with_zone->", data_with_zone)

    # Aggregate the Data based on ZoneId, DeviceType, Datatype and Timestamp
    aggr_data = get_aggeregate_data(data_with_zone)
    print("Output Data is ->", aggr_data)

    THRESHOLD_HUMIDITY = 10.0
    for record in aggr_data:
        if (float(record['average']) < THRESHOLD_HUMIDITY):
            print ("Soil Humidity is very Lower - ", record['average'], "% than the Thrshold - ", str(THRESHOLD_HUMIDITY), "%. Switch on the Sprinkler in Zone - ", record['zoneId'])
        newRecord = {
            "zoneId": {"S": str(record['zoneId'])},
            "deviceType": {"S": record['deviceType']},
            "dataType": {"S": record['dataType']},
            "timestamp": {"S": timestamp},
            "avgValue": {"S": str(record['average'])},
        }
        save_stat = insertIntoAggrDynamoTable(db_name, newRecord)
        print(save_stat)

    print ("End Lambda")
