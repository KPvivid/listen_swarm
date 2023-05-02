#!/usr/bin/env python

import numpy as np
import subprocess
import os
import threading
import time

from pathlib import Path
from crazyflie_py import *
from crazyflie_py.uav_trajectory import Trajectory

# declare variable for directory
gen_traj_binary_path =  Path(__file__).parent / 'gen_trajectory'
data_directory = Path(__file__).parent / "data"
v_max = 1.0
a_max = 1.0
TIMESCALE = 0.5
cf_num = 8

class waypoints_monitor(threading.Thread):
    """
    A class used for monitoring a waypoints file and update the trajectory file if the waypoints file change
    """
    def __init__(self, waypoints_file, trajectory_file, condition, name):
        super().__init__()
        self.waypoints_file = data_directory / waypoints_file
        self.trajectory_file = data_directory / trajectory_file
        self.condition = condition
        self.last_modified_time = os.stat(self.waypoints_file).st_mtime
        self.name = name

    """
    Make the trajectory file
    """
    def make_traj(self):
        subprocess.run([gen_traj_binary_path, "-i", self.waypoints_file, "--v_max", str(v_max), "--a_max", str(a_max), "-o", self.trajectory_file])
 

    """
    Notify the controller if the waypoint file has changed
    """
    def run(self):
        while True:
            current_modified_time = os.stat(self.waypoints_file).st_mtime
            if current_modified_time != self.last_modified_time:
                print(f'Drone {self.name} is moving')
                self.make_traj()
                self.last_modified_time = current_modified_time
                with self.condition:
                    self.condition.notify()

def cf_controller(cf, monitor, traj, time_helper, name):
    """
    Waiting for the signal from the monitor, and send the signal to the server
    """
    print("Drone", name, "waiting for command")
    while True:
        with monitor.condition:
            monitor.condition.wait()
            traj.loadcsv(monitor.trajectory_file)
            cf.uploadTrajectory(0, 0, traj)
            time_helper.sleep(0.1)
            cf.startTrajectory(0, timescale=TIMESCALE)

def main():
    # connect to the server
    swarm = Crazyswarm()

    # initilize variable
    time_helper = swarm.timeHelper
    allcfs = swarm.allcfs
    condition = [None] * cf_num
    cf = [None] * cf_num
    monitor = [None] * cf_num
    traj = [None] * cf_num
    controller = [None] * cf_num

    print(gen_traj_binary_path)
    print(data_directory)

    # takeoff
    allcfs.takeoff(targetHeight=1.0, duration=0.01)
    
    for i in range(0, cf_num):
        # make all the condition listener base on the csv
        condition[i] = threading.Condition()
        monitor[i] = waypoints_monitor("waypoint" + str(i) + ".csv", "traj" + str(i) + ".csv", condition[i], str(i))
        monitor[i].start()
        cf[i] = allcfs.crazyflies[i]
        traj[i] = Trajectory()
        controller[i] = threading.Thread(target=cf_controller, args=(cf[i], monitor[i], traj[i], time_helper, str(i)))
        controller[i].start()

    for i in range(0, cf_num):
        monitor[i].join()
        controller[i].join()

    allcfs.land(targetHeight=0.06, duration=2.0)
    time_helper.sleep(3.0)


if __name__ == "__main__":
    main()
