#!/usr/bin/env python

import socket
import sys
from threading import Thread
import time
import datetime
import os

# server host + port
SERVER_HOST = "192.168.0.6"
SERVER_PORT = 8080

# client host + port
PORT = 10000

TOTAL_LOGS = 0

# format date
date_now = datetime.datetime.fromtimestamp(time.time())
date_now = str(date_now).replace(":", "_", 3)
date_now = date_now.replace(".", "_", 1)
date_now = date_now.replace(" ", "_", 1)

# check if directory exists
if not os.path.isdir("logs"):
    os.mkdir("logs")

# name of log file
FILE_NAME = ("logs/log" + date_now + ".csv")

# open and append to log file
log = open(FILE_NAME, "a")
log.write("Client No.,Client Host,Client Port,Number of Requests,Amount of Data Sent to Server,Amount of Time Taken (sec)\n")

def handle_logs(num_client: int):
    while True:
        if TOTAL_LOGS == num_client:
            break

    log.flush()
    log.close()

def create_client(cid: int, host: str, port: int, message: str, num_send: int):
    # create socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client.bind((host, port))
    client.connect((SERVER_HOST, SERVER_PORT))
    
    # start time
    time_start = time.time()

    index = 0

    while (index < int(num_send)):
        try:
            # send input to server
            
            client.send((message + "\n").encode("utf-8"))
            
            data = client.recv(1024).decode()

            if not data:
                sys.exit(0)

            index += 1
        except ConnectionResetError:
            index -= 1
            pass
    
    client.send(("quit\n").encode("utf-8"))
    data = client.recv(1024).decode()
    
    # end time
    time_end = time.time()

    # time taken
    time_taken = time_end - time_start

    data_size_sent = len(message + "\n") * int(num_send)

    # format log message
    log_message = '%s,%s,%s,%s,%s,%s' % (str(cid), "192.168.0.5", str(port), str(num_send), str(data_size_sent), str(time_taken))
    
    log.flush()
    log.write(log_message + "\n")
    
    global TOTAL_LOGS
    TOTAL_LOGS += 1

if __name__ == "__main__":
    host        = input("Enter host number: ")
    num_client  = input("Enter number of client(s): ")
    message     = input("Enter a message: ")
    num_send    = input("Number of times to send message: ")

    threads = []

    try:
        logger_thread = Thread(target=handle_logs, args=(int(num_client),))
        logger_thread.start()

        cid = 0

        for x in range(int(num_client)):
            # create a thread for each client
            cid += 1
            PORT += 1

            print("Creating Client: " + str(PORT))

            threads.append(Thread(target=create_client, args=(cid, host, PORT, message, num_send,)))
            threads[x].start()
            
    except KeyboardInterrupt as e:
        print("Server Shutdown")

        for x in range(int(num_client)):
            threads[x].exit()

        exit()
