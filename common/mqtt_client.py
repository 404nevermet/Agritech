from logging import root
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishTimeoutException
from AWSIoTPythonSDK.core.protocol.internal.defaults import DEFAULT_OPERATION_TIMEOUT_SEC
from common.application_constants import ApplicationConstants
from common.config_reader import ConfigReader

# Wrapper over AWS MQTT client to read configuration from file and simplify interface


class MQTTClient:
    def __init__(self, clientId, rootCAPath=None, privateKeyPath=None, caCertificatePath=None, host=None, port=None, useWebSockets=False) -> None:
        self._config = ConfigReader.get_config(
            ApplicationConstants.CONFIG_MQTT_FILE)

        if bool(host):
            self._host = host
        else:
            self._host = self._config[ApplicationConstants.MQTT_CONFIG_PARAMETER_HOST]

        if bool(port):
            self._port = port
        else:
            self._port = self._config[ApplicationConstants.MQTT_CONFIG_PARAMETER_PORT]

        if bool(rootCAPath):
            self._rootCAPath = rootCAPath
        else:
            self._rootCAPath = self._config[ApplicationConstants.CONFIG_PARAMETER_ROOT_CA_PATH]

        if bool(caCertificatePath):
            self._caCertificatePath = caCertificatePath
        else:
            self._caCertificatePath = self._config[ApplicationConstants.CONFIG_PARAMETER_CA_CERT_PATH]

        if bool(privateKeyPath):
            self._privateKeyPath = privateKeyPath
        else:
            self._privateKeyPath = self._config[ApplicationConstants.CONFIG_PARAMETER_PRIVATE_KEY_PATH]

        self._qos = 1  # Default to 1

        if(useWebSockets):
            self._client = AWSIoTMQTTClient(clientId, useWebsocket=True)
            self._client.configureEndpoint(self._host, self._port)
            self._client.configureCredentials(self._rootCAPath)
        else:
            self._client = AWSIoTMQTTClient(clientId)
            self._client.configureEndpoint(self._host, self._port)
            self._client.configureCredentials(
                self._rootCAPath, self._privateKeyPath, self._caCertificatePath)

        # AWSIoTMQTTClient connection configuration
        self._client.configureAutoReconnectBackoffTime(1, 32, 20)
        # Infinite offline Publish queueing
        self._client.configureOfflinePublishQueueing(-1)
        self._client.configureDrainingFrequency(2)  # Draining: 2 Hz
        self._client.configureConnectDisconnectTimeout(10)  # 10 sec
        self._client.configureMQTTOperationTimeout(5)  # 5 sec

    def connect(self):
        return self._client.connect()

    def subscribe(self, topic, callback):
        self._client.subscribe(topic, 1, callback)

    def publish(self, topic, message):
        self._client.publish(topic, message, 1)  # Default Qos is 1 for now

    def disconnect(self):
        self._client.disconnect()
