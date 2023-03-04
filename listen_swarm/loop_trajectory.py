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
cf_num = 2

class waypoints_monitor(threading.Thread):
    """
    A class used for monitoring a waypoints file and update the trajectory file if the waypoints file change
    """
    def __init__(self, waypoints_file, trajectory_file, condition):
        super().__init__()
        self.waypoints_file = data_directory / waypoints_file
        self.trajectory_file = data_directory / trajectory_file
        self.condition = condition
        self.last_modified_time = os.stat(self.waypoints_file).st_mtime

    def make_traj(self):
        subprocess.run([gen_traj_binary_path, "-i", self.waypoints_file, "--v_max", str(v_max), "--a_max", str(a_max), "-o", self.trajectory_file])
 
    def run(self):
        while True:
            current_modified_time = os.stat(self.waypoints_file).st_mtime
            if current_modified_time != self.last_modified_time:
                print(f'{self.waypoints_file} has been modified')
                self.make_traj()
                print(f'{self.trajectory_file} has been updated')
                self.last_modified_time = current_modified_time
                with self.condition:
                    self.condition.notify()
            time.sleep(0.5)

def cf_controller(cf, monitor, traj, time_helper):
    while True:
        with monitor.condition:
            print(cf, "waiting for command")
            monitor.condition.wait()
            print("received a signal!")
            traj.loadcsv(monitor.trajectory_file)
            time_helper.sleep(1)
            cf.uploadTrajectory(0, 0, traj)
            time_helper.sleep(1)
            cf.startTrajectory(0, timescale=TIMESCALE)
            time_helper.sleep(traj.duration * TIMESCALE + 0.5)

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
        condition[i] = threading.Condition()
        monitor[i] = waypoints_monitor("waypoint" + str(i) + ".csv", "traj" + str(i) + ".csv", condition[i])
        monitor[i].start()
        cf[i] = allcfs.crazyflies[i]
        traj[i] = Trajectory()
        controller[i] = threading.Thread(target=cf_controller, args=(cf[i], monitor[i], traj[i], time_helper))
        controller[i].start()

    for i in range(0, cf_num):
        monitor[i].join()
        controller[i].join()

    allcfs.land(targetHeight=0.06, duration=2.0)
    time_helper.sleep(3.0)


if __name__ == "__main__":
    main()
