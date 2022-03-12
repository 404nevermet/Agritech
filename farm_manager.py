
from simulators.sprinkler import Sprinkler
from common.application_constants import ApplicationConstants
from common.DataTable import DataTable
from simulators.soilsensor import SoilSensor


class FarmManager:
    def __init__(self, soil_sensors_count, sprinkler_count):
        self._soil_censors_count = soil_sensors_count
        self._sprinkler_count = sprinkler_count
        self._devices = []
        self.create_soil_sensor_devices()
        self.create_sprinkler_devices()
        self._data_table = DataTable()

    def create_soil_sensor_devices(self):
        for count in range(0, self._soil_censors_count):
            deviceId = "SMS-00{}".format(count)
            soilMoistureSensor = SoilSensor(deviceId, 1, 1, 1)
            self._devices.append(soilMoistureSensor)

    def create_sprinkler_devices(self):
        for count in range(0, self._soil_censors_count):
            deviceId = "SLR-00{}".format(count)
            sprinkler = Sprinkler(deviceId, 1, 1, 1)
            self._devices.append(sprinkler)

    def start_all(self):
        for index in range(len(self._devices)):
            self._devices[index].start()

    def stop_all_devices(self):
        for device in self._devices:
            device.stop()

    def wait_for_all(self):
        for device in self._devices:
            device.join()

    def get_all_messages(self):
        data = []
        for device in self._devices:
            if(device.get_device_type() == ApplicationConstants.DEVICE_TYPE_SPRINKLER):
                continue
            data.append(device.get_message())
        return data

    def print_console(self):
        data = self.get_all_messages()
        self._data_table.print_table(data)
        pass

    def execute(self):
        self.start_all()
        try:
            while True:
                self.print_console()

        except KeyboardInterrupt:
            self.stop_all_devices()
            print("Closing Simulation")
        finally:
            pass


def main():
    farmManager = FarmManager(10,2)
    farmManager.execute()


if __name__ == "__main__":
    main()
