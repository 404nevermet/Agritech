import time
import sched

class Schedular:
    def __init__(self, simulator, frequency) -> None:
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._simulator = simulator

        self._frequency = frequency
        self._startTime = None
        self._needStop = False

    # Given a simulation object it schedules the task method at a given frequency
    def schedule(self):
        self._startTime = time.time()
        nextSecond = self._frequency
        while not self._needStop:
            try:
                self._scheduler.enterabs(
                    self._startTime + nextSecond, 1, self._simulator.task, ())

                nextSecond += self._frequency

                self._scheduler.run()
            except KeyboardInterrupt:
                break
    
    # Provides an interfce for external classes to stop the schedular
    def stop(self):
        print("Stoping device : {} simulation task".format(self._simulator.get_divice_id()))
        self._needStop = True

