import rp
from rp_overlay import overlay
import socket
import os
import time
import numpy as np
import signal

""" Class to handle the process killing with kill -15. It will release the RP resources when the process is killed. """
class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGTERM, self.exit_gracefully) # SIGTERM = kill -15

  def exit_gracefully(self, signum, frame):
    self.kill_now = True

# User target
lambda_max = 530.2998688227693
lambda_min = 530.2986113722394
lambda_target = (lambda_max+lambda_min)/2

# Save error evolution
error_filename = "Saved_data/Error_evolution_2025_10_17_11h.txt"
time_step = 500 # ms

# Initialize connection with WLM
HOST = "10.44.1.21"  # The server's hostname or IP address
PORT = 3601  # The port used by the server

# PID coeff
k_int = 1e2
u = 0 # Start far from the target wavelength

if __name__ == "__main__":
    # Initialize RP
    fpga = overlay()
    rp.rp_Init()
    rp.rp_GenReset()
    channel = rp.RP_CH_1
    waveform = rp.RP_WAVEFORM_DC

    # Create saving folder
    if not(os.path.isdir("Saved_data")):
        os.mkdir("Saved_data")

    t_start = time.time()

    killer = GracefulKiller()

    while not killer.kill_now: # While the process is not killed, perform the PID
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            data = sock.recv(1024).decode().split(";")[3]
            print("Lambda = "+str(data)+" nm")
            error = lambda_target-float(data)
            print("Error = "+str(error)+" nm")
            u += error*k_int

            # Boundary conditions
            if u > 1:
                u = 1
            if u < 0:
                u = 0

            rp.rp_GenWaveform(channel, waveform)
            rp.rp_GenAmp(channel, abs(u))
            rp.rp_GenOutEnable(channel)
            rp.rp_GenTriggerOnly(channel)

            # Print/save error signal
            print("u(t) = "+str(u)+" V")
            with open(error_filename, "a") as file:
                file.write(str(time.time()-t_start)+";"+str(data)+";"+str(error)+";"+str(u)+"\n")

    print("Process killed, releasing RP resources.")
    rp.rp_Release()
