
from simulators.sprinkler import Sprinkler


def main():
    deviceId = "SLR-00{}".format(1)
    sprinkler = Sprinkler(deviceId,1, 1, 1)    
    sprinkler.start()
    sprinkler.join()

if __name__ == "__main__":
    main()
