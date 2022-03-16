class ApplicationConstants:

    # Configuration literals
    CONFIG_MQTT_FILE = "./Config/mqtt_config.json"

    # Simulator Config
    CONFIG_SOILSENSOR_FILE = "./Config/soilsensor_config.json"
    CONFIG_SPRINKLER_FILE = "./Config/sprinkler_config.json"

    # Configuration parameters
    MQTT_CONFIG_PARAMETER_HOST = "host"
    MQTT_CONFIG_PARAMETER_PORT = "port"

    CONFIG_PARAMETER_ROOT_CA_PATH = "rootCAPath"
    CONFIG_PARAMETER_CA_CERT_PATH = "caCertPath"
    CONFIG_PARAMETER_PRIVATE_KEY_PATH = "privateKeyPath"


    SENSOR_CONFIG_PARAMETER_MOISTURE_DATA = "moistureData"
    SENSOR_CONFIG_PARAMETER_MIN = "min"
    SENSOR_CONFIG_PARAMETER_MAX = "max"
    SENSOR_CONFIG_PARAMETER_MEAN = "mean"
    SENSOR_CONFIG_PARAMETER_STANDARD_DEVIATION = "standardDeviation"
    SENSOR_CONFIG_PARAMETER_DATA_GENERATION_FREQUENCY = "dataGenerationFrequency"
    # Message fileds
    FIELD_STATE = "state"

    # Device Types
    DEVICE_TYPE_SOIL_MOISTURE_SENSOR = "SoilMoistureSensor"
    DEVICE_TYPE_SPRINKLER = "Sprinkler"





    
