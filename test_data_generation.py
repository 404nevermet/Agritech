from cProfile import label
from  datetime import datetime, timedelta
import random
from time import sleep
import boto3 
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr


DYNAMODB_SPRINKLER_STATE_TABLE = "sprinkler_state"
DYNAMODB_AGGREGATE_DATA_TABLE ="aggregate_data"

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
        entry = table.query(
            KeyConditionExpression=Key(keyName).eq(keyValue)
        )["Items"][0]

        # entry = table.get_item(Key={'pkey': keyValue})
        entry[updatKey]  = updateValue
        return table.put_item(Item=entry)

def aggregate_data(data):
    intermediate_aggregated_data = {}
    # Format 
    # {
    #   "zoneId" {
    #       "2021-11-12T09:30:00Z": {
    #           "datatype": "Humidity",
    #           "value": [50,60,55,63]
    #       }
    #   }
    
    for entry in data:
        time_truncated_to_minutes = datetime.strptime(
                entry['timestamp'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%dT%H:%M:00Z')
        zoneId = entry['zoneId']
        value = entry['value']
        if not zoneId in intermediate_aggregated_data.keys():
            intermediate_aggregated_data[zoneId] = {}
        if not time_truncated_to_minutes in intermediate_aggregated_data[zoneId].keys():
            intermediate_aggregated_data[zoneId][time_truncated_to_minutes] = {}
            intermediate_aggregated_data[zoneId][time_truncated_to_minutes]['values'] = []
    
        intermediate_aggregated_data[zoneId][time_truncated_to_minutes]['values'].append(value)
    
    # Flaten the data
    # Format 
    # [
    #   {"zoneId":<>,"datatype": "Humidity","timestamp":"2021-11-12T09:30:00Z", "value":50},
    #   ....
    # ]
    aggregated_data = []
    for zoneId in intermediate_aggregated_data.keys():
        for timestamp in intermediate_aggregated_data[zoneId].keys():
            entry = {}
            entry['zoneId'] = zoneId
            entry['dataType'] = "Humidity"
            entry["deviceType"] = "SoilSensor"
            entry['timestamp'] = timestamp
            values = intermediate_aggregated_data[zoneId][timestamp]['values']
            
            entry['value'] = "{:0.2f}".format(sum(values)/len(values))
            aggregated_data.append(entry)

    return aggregated_data

def round_to_two_digits(number):
    if number < 10 :
       return "0{}".format(number)
    else:
        return number
def get_raw_data_entry(zoneId, value, timestamp):
    data = {}
    data['zoneId'] = zoneId
    data['dataType'] = 'Humidity'
    data['deviceType'] = 'SoilSensor'
    data['timestamp'] = timestamp
    data['value'] = float(value)
    return data

def generate_graph_data(data):
    labels = [ entry['timestamp'] for entry in data if entry['zoneId'] == data[0]['zoneId']]
    deviceWiseData = {}
    for entry in data:
        if not entry['zoneId'] in deviceWiseData.keys():
            deviceWiseData[entry['zoneId']] = []
        deviceWiseData[entry['zoneId']].append(entry['value'])
    
    print(labels)
    print(deviceWiseData)
    return (labels,deviceWiseData )


# Update table test 
def test_update_db_entry():
    dbUtil = DynamoDBUtil()
    val = dbUtil.update_entry(DYNAMODB_SPRINKLER_STATE_TABLE,'deviceId','SPL-002','state','ON')
    print(val)

# Create sprinklers state table
def test_generate_sprinkler_state_table():
    dbUtil =  DynamoDBUtil()
    dbUtil.create_table_if_not_exist(DYNAMODB_SPRINKLER_STATE_TABLE,"deviceId", 'S', 'timestamp', 'S')

    sprinklers = []
    for counter in range(4):
        sprinkler_state = {}
        sprinkler_state['deviceId']  = "SPL-00{}".format(counter + 1)
        sprinkler_state['zoneId']  = "{}".format(counter + 1)
        sprinkler_state['state']  = 'OFF'
        sprinkler_state['timestamp'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        sprinklers.append(sprinkler_state)
    
    print(sprinklers)

    dbUtil.bulk_insert("sprinkler_state",sprinklers)

# Generating data for graph demo
def test_generate_graph_data_from_aggregate_data():
    aggregated_data = test_generate_aggregate_data_for_hours(10)
    graph_data = generate_graph_data(aggregated_data)
    print(graph_data) 

def generate_data_for_date_and_hours(zone, currentdate, start_hour, end_hour):
    raw_data = []
    for hours in range(start_hour ,end_hour):
        for minutes in range(60):
            for senconds in range(60):
                zoneId = "Z-00{}".format(zone + 1)
                value = "{:0.2f}".format(round(random.randrange(50,65,2),2))
                this_second_time = "{}T{}:{}:{}Z".format(currentdate,round_to_two_digits(hours),round_to_two_digits(minutes),round_to_two_digits(senconds))
                data = get_raw_data_entry(zoneId, value, this_second_time)

                raw_data.append(data)
    return raw_data

# Generating aggregate data for next n hours
def test_generate_aggregate_data_for_hours(num_hours):
    dbUtil =  DynamoDBUtil()
    #dbUtil.create_table_if_not_exist(DYNAMODB_AGGREGATE_DATA_TABLE, 'zoneId','S')

    date_time_now = datetime.now()
    currentdatetime = date_time_now.strftime("%Y-%m-%dT%H:%M:%SZ")
    currentdate = currentdatetime.split('T')[0]
    start_hour = int(currentdatetime.split('T')[1].split(":")[0])
    end_hour = start_hour + num_hours
    tuples = []
    if end_hour > 24:
        next_day = (date_time_now + timedelta(hours=num_hours)).strftime('%Y-%m-%d')
        tuples.append((currentdate, start_hour, 23))
        tuples.append((next_day, 0, end_hour - 24))
    else:
        tuples.append((currentdate, start_hour, 23))
    
    raw_data = []
    for zone in range(4):
        for day_time_tuple in tuples:
            days_data = generate_data_for_date_and_hours(zone, day_time_tuple[0], day_time_tuple[1], day_time_tuple[2])
            raw_data.extend(days_data)

    aggregated_data = aggregate_data(raw_data)
    print(aggregated_data)

    #dbUtil.bulk_insert(DYNAMODB_AGGREGATE_DATA_TABLE, aggregated_data)
    
    return aggregated_data

def test_data_between_dates():
    start_time = (datetime.now() - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

    
    dbUtil =  DynamoDBUtil()
    data = dbUtil.get_data_between_time_range(DYNAMODB_AGGREGATE_DATA_TABLE, start_time, end_time)

    return data

def main():
    test_generate_graph_data_from_aggregate_data()
    # test_data_between_dates()
    # test_generate_aggregate_data_for_hours(10)

    # test_generate_graph_data_from_aggregate_data()
    # test_update_db_entry()
    # test_generate_sprinkler_state_table()


if __name__ == "__main__":
    main()
