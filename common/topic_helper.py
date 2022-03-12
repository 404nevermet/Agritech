# This file is created to servce following purposes:
# 1. Centralized topic structure/patterns to make it easy to change and maintain
# 2. Provide Helper class with helper methods that can be used by server and client to get appropriate topics names
#    This helps the both server and clients to be in sync with changes done to topics

# Root level design for topics.
# This devides topics to 3 broad categoreis Requests, Commands, ControlCommands and their respective shadow topics
class Topics:
    SENSOR_REQUEST = "sensor/request/"
    SENSOR_RESPONSE = "sonsor/response/"
    SENSOR_DATA = "sensor/data"

    ACTUATOR_REQUEST = "actuator/request/"
    ACTUATOR_RESPONSE = "actuator/response/"
    ACTUATOR_COMMAND = "actuator/command/"



# This contains third level of request topic and represents type of request
class RequestType:
    REQUEST_REGISTER = "register"


# This contains third level of command topic and represents type of command
class CommandType:
    COMMAND_SET_STATE = "set-state"

class DataType:
    DATA_TELEMETRY = "telemetry"


# This is helper class to provide topic names for Sensor class
# This basically localize the changes in case we need changes to topic structure
class SoilSensorTopicHelper:
    @staticmethod
    def get_register_request_topic():
        return "{}{}".format(Topics.SENSOR_REQUEST, RequestType.REQUEST_REGISTER)

    @staticmethod
    def get_register_request_reponse_topic(device_id):
        return "{}{}/{}".format(Topics.SENSOR_RESPONSE, RequestType.REQUEST_REGISTER,device_id)

    @staticmethod
    def get_telemetry_data_topic():
        return "{}".format(Topics.SENSOR_DATA)


# This is helper class to provide topic names for Sprinkler class
# This basically localize the changes in case we need changes to topic structure
class SprinklerTopicHelper:
    @staticmethod
    def get_register_request_topic():
        return "{}{}".format(Topics.ACTUATOR_REQUEST, RequestType.REQUEST_REGISTER)

    @staticmethod
    def get_register_request_reponse_topic(zone_id):
        return "{}{}/{}".format(Topics.ACTUATOR_RESPONSE, RequestType.REQUEST_REGISTER,zone_id)

    @staticmethod
    def get_set_state_command_topic(zone_id):
        return "{}{}/{}".format(Topics.ACTUATOR_COMMAND, CommandType.COMMAND_SET_STATE, zone_id)

    @staticmethod
    def get_set_state_command_response_topic(zone_id):
        return "{}{}/{}".format(Topics.ACTUATOR_RESPONSE, CommandType.COMMAND_SET_STATE,zone_id)
