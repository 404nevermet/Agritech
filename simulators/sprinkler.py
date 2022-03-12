
from common.schedular import Schedular
from common.application_constants import ApplicationConstants
from common.config_reader import ConfigReader
from common.topic_helper import SprinklerTopicHelper
from simulators.simulator import Simulator


class Sprinkler(Simulator):

    _SPRINKLER_STATES = ["OFF", "ON"]

    def __init__(self, deviceId, lattitude, longitude, zoneId) -> None:
        super().__init__(deviceId, ApplicationConstants.DEVICE_TYPE_SPRINKLER,
                         lattitude, longitude, zoneId)

        self._state = self._SPRINKLER_STATES[0]

        # Create Schedular and start publishing simulationn data
        self._schedular = Schedular(self, 1)

    def run(self):
        print(f"Sarting Sprinkler-{self.get_divice_id()}")
        self._schedular.schedule()

    # Scheduled task - Do nothing
    def task(self):
        pass

    # Stop scheduled task
    def stop(self):
        self._schedular.stop()

    def publish(self, topic, message):
        return super().publish(topic, message)

    def subscribe(self, topic, callback):
        return super().subscribe(topic, callback)

    def read_config(self):
        self._config = ConfigReader.get_config(
            ApplicationConstants.CONFIG_SPRINKLER_FILE)

    def _subscribe_to_required_topics(self):
        # Sprinker is interested in listening to

        # register request response
        self.subscribe(
            SprinklerTopicHelper.get_register_request_reponse_topic(self._device_id), self.onRegister)

        # Commands to set state
        self.subscribe(SprinklerTopicHelper.get_set_state_command_topic(
            self._zone_id), self.onCommand)

    # Callbacks
    def onCommand(self, client, userdata, message):
        payload = self._get_payload(message)
        self._lock.acquire()
        self._message = payload
        self._lock.release()
        print(payload)
        state = payload[ApplicationConstants.FIELD_STATE]
        if(state in self._SPRINKLER_STATES):
            self._state = state