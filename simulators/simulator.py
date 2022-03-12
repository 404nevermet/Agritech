
import json
from common.mqtt_client import MQTTClient
import threading


class Simulator(threading.Thread):
    def __init__(self, deviceId, deviceType, lattitude, longitude, zoneId) -> None:
        super().__init__(name=deviceId)
        self._device_id = deviceId
        self._device_type = deviceType
        self._lattitude = lattitude
        self._longitude = longitude
        self._zone_id = zoneId
        self._message = None
        self._lock = threading.RLock()

        # Read simulator config
        self.read_config()

        # TODO - Work on actual certs and mqtt config
        self._mqtt_client = MQTTClient(self._device_id)

        # Connect with MQTT
        if(self.connect()):
           # On successfull connect  subscribe to all required topics to communicate with IoT Core
           self._subscribe_to_required_topics()

    def get_divice_id(self):
        return self._device_id

    def get_device_type(self):
        return self._device_type

    def get_message(self):
        if(bool(self._message)):
            return self._message
        else:
            return self.get_default_message()

    def get_default_message(self):
        pass

    async def run(self):
        pass

    def task(self):
        pass

    def connect(self, callback=None, arguments=None):
        return self._mqtt_client.connect()

    def publish(self, topic, message):
        self._mqtt_client.publish(topic, message)

    def subscribe(self, topic, callback):
        self._mqtt_client.subscribe(topic, callback)

    def read_config(self):
        pass

    # Callbacks
    def onRegister(self, client, userdata, message):
        response = self._get_payload(message)
        print(response)

    def _handle_register_request_responses(self, message):
        response = json.loads(message.payload.decode("utf-8"))

    # All the subscriptions that device is interested in.
    def _subscribe_to_required_topics(self):
        pass

    def _get_payload(self, message):
        return json.loads(message.payload.decode("utf-8"))
