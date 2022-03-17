import json
import random
import datetime
from sqlite3 import Timestamp

from prompt_toolkit import Application
from common.application_constants import ApplicationConstants
from common.config_reader import ConfigReader
from common.schedular import Schedular
from common.topic_helper import SoilSensorTopicHelper
from simulators.simulator import Simulator


class SoilSensor(Simulator):
    def __init__(self, deviceId, lattitude, longitude, zoneId) -> None:
        super().__init__(deviceId, ApplicationConstants.DEVICE_TYPE_SOIL_MOISTURE_SENSOR,
                         lattitude, longitude, zoneId)

        # Create Schedular and start publishing simulationn data
        self._schedular = Schedular(self, self._data_generation_frequency)

    def get_default_message(self):
        message = {}
        message["deviceId"] = "Not Publised Yet"
        message["deviceType"] = self._device_type
        message['datatype'] = 'SoilHumidity'
        message["value"] = "Not Publised Yet"
        message["timestamp"] = self._get_timestamp()
        return message

    # Runs the task in schedular
    def run(self):
        print(f"Starting Sensor-{self.get_divice_id()}")
        self._schedular.schedule()
    
    # scheduled task
    def task(self):
        # Get topic to pushlish telemetric data
        topic = self.get_telemety_data_topic()
        # Get payload before publishing
        payload = self.get_payload()
        self.publish(topic, payload)

    # Stop scheduled task
    def stop(self):
        self._schedular.stop()

    def publish(self, topic, message):
        return super().publish(topic, message)

    def subscribe(self, topic, callback):
        return super().subscribe(topic, callback)

    def register(self):
        super().register()

    def read_config(self):
        self._config = ConfigReader.get_config(
            ApplicationConstants.CONFIG_SOILSENSOR_FILE)
        self._min = self._config[ApplicationConstants.SENSOR_CONFIG_PARAMETER_MOISTURE_DATA][ApplicationConstants.SENSOR_CONFIG_PARAMETER_MIN]
        self._max = self._config[ApplicationConstants.SENSOR_CONFIG_PARAMETER_MOISTURE_DATA][ApplicationConstants.SENSOR_CONFIG_PARAMETER_MAX]
        self._mean = self._config[ApplicationConstants.SENSOR_CONFIG_PARAMETER_MOISTURE_DATA][ApplicationConstants.SENSOR_CONFIG_PARAMETER_MEAN]
        self._standardDeviation = self._config[ApplicationConstants.SENSOR_CONFIG_PARAMETER_MOISTURE_DATA][
            ApplicationConstants.SENSOR_CONFIG_PARAMETER_STANDARD_DEVIATION]
        self._data_generation_frequency = self._config[ApplicationConstants.SENSOR_CONFIG_PARAMETER_DATA_GENERATION_FREQUENCY]

    # All the subscriptions that device is interested in.
    def _subscribe_to_required_topics(self):
        # Sensor is interested in listening to
        # register request response
        self.subscribe(
            SoilSensorTopicHelper.get_register_request_reponse_topic(self._device_id), self.onRegister)

    def get_telemety_data_topic(self):
        return SoilSensorTopicHelper.get_telemetry_data_topic()

    def get_register_device_topic(self, deviceId):
        return SoilSensorTopicHelper.get_register_request_topic(deviceId)

    def _get_sensed_parameter(self):
        return round(float(random.normalvariate(self._mean, self._standardDeviation)), 1)

    def get_payload(self):
        """
        Message Structure
        -----------------
        {
            deviceId:<Device Id>,
            deviceType: <Device Type>,
            temperatur:<Temperatur>,
            humidity:<Humidity>
        }
        """
        timestamp = self._get_timestamp()
        message = {}
        message["deviceId"] = self._device_id
        message["deviceType"] = self._device_type
        message['datatype'] = 'SoilHumidity'
        message["value"] = self._get_sensed_parameter()
        message["timestamp"] = timestamp

        self._lock.acquire()
        self._message = message
        self._lock.release()

        # return print("{}".format(self._message))
        return json.dumps(message)

