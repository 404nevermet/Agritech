import json

class ConfigReader:

    @staticmethod
    def _read_config(filePath):
        f = open(filePath)
        config = json.loads(f.read())
        f.close()
        return config

    @staticmethod
    def get_config(filePath):
        return ConfigReader._read_config(filePath)
