#!/usr/bin/env python

from __future__ import print_function
from contextlib import contextmanager
import datetime
import os
from queue import Queue
import select
import socket
import sys
from threading import Thread
import time

ServerPort = 8080   # Listening port
MAXCONN = 5         # Maximum connections
BUFLEN = 80         # Max buffer size

DEBUG = True

date_now = datetime.datetime.fromtimestamp(time.time())
date_now = str(date_now).replace(":", "_", 3).replace(".", "_", 1).replace(" ", "_", 1)

def logData(queue):
  if not os.path.isdir("server_logs"):
    os.mkdir("server_logs")

  logFile = open("server_logs/server_log" + date_now + ".csv", "w")
  logFile.flush()

  while True:
    info = queue.get()

    if info == "kill":
      break

    logFile.write(info)
    logFile.flush()
  logFile.close()
  
  return

dataQueue = Queue()
logDataThread = Thread(target=logData, args=(dataQueue,))
logDataThread.start()

Statistics = {}

#----------------------------------------------------------------------------------------------------------------
# Main server function 
def EpollServer (socket_options, address):
    
    with socketcontext (*socket_options) as server, epollcontext (server.fileno(), select.EPOLLIN) as epoll:
        server.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # Allow multiple bindings to port
        server.bind(address)
        server.listen (MAXCONN)
        server.setblocking (0)
        server.setsockopt (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)   # Set socket to non-blocking
        print ("Listening on Port:",ServerPort)

        dataQueue.put('client,requests,data sent (bytes)\n')

        Client_SD = {}
        Client_Reqs = {}
        Server_Response = {}
        
        server_SD = server.fileno()

        while True:
            events = epoll.poll(1) # keep checking for events from clients

            for sockdes, event in events:
                if sockdes == server_SD:
                    init_connection (server, Client_SD, Client_Reqs, Server_Response, epoll)
                elif event & select.EPOLLIN:
                    Receive_Message (sockdes, Client_Reqs, Client_SD, Server_Response, epoll)
                elif event & select.EPOLLOUT:
                    Echo_Response (sockdes, Client_SD, Server_Response, epoll)

#----------------------------------------------------------------------------------------------------------------
# Process Client Connections
def init_connection (server, Client_SD, Client_Reqs, Server_Response, epoll):
    connection, address = server.accept()
    connection.setblocking(0)
    
    if DEBUG:
        print ('Client Connected:', address)    #print client IP

    fd = connection.fileno()
    epoll.register(fd, select.EPOLLIN)
    Client_SD[fd] = connection
    Server_Response[fd] = ''
    Client_Reqs[fd] = ''
    
    # fd = name
    # num_req
    # data_size
    Statistics[str(address[1])] = [address, 0, 0]

#----------------------------------------------------------------------------------------------------------------
# Receive a request and send an ACK with echo
def Receive_Message (sockdes, Client_Reqs, Client_SD, Server_Response, epoll):
    
    Client_Reqs[sockdes] += Client_SD[sockdes].recv (BUFLEN).decode()

    # TEST
    print("Client_SD")
    print(Client_SD[sockdes])
    print("Client_Reqs")
    print(Client_Reqs[sockdes])
    # Make sure client connection is still open    
    if Client_Reqs[sockdes] == 'quit\n' or Client_Reqs[sockdes] == '':
        if DEBUG:
            print('[{:02d}] Client Connection Closed!'.format(sockdes))
        
        Client_SD[sockdes].close()
        epoll.unregister(sockdes)

        del Client_SD[sockdes], Client_Reqs[sockdes], Server_Response[sockdes]
        return

    elif '\n' in Client_Reqs[sockdes]:
        epoll.modify(sockdes, select.EPOLLOUT)
        msg = Client_Reqs[sockdes][:-1]

        if DEBUG:
            print("[{:02d}] Received Client Message: {}".format (sockdes, msg))
        
        # ACK + received string
        # Server_Response[sockdes] = 'ACK => ' + Client_Reqs[sockdes]
        Server_Response[sockdes] = Client_Reqs[sockdes]
        Client_Reqs[sockdes] = ''

        c_port = str(Client_SD[sockdes].getpeername()[1])
        Statistics[c_port][1] += 1
#----------------------------------------------------------------------------------------------------------------
# Send a response to the client
def Echo_Response (sockdes, Client_SD, Server_Response, epoll):
    byteswritten = Client_SD[sockdes].send(Server_Response[sockdes].encode())
    Server_Response[sockdes] = Server_Response[sockdes][byteswritten:]
    
    # TEST
    print("Server_Response")
    print(Server_Response[sockdes])
    
    epoll.modify(sockdes, select.EPOLLIN)

    c_port = str(Client_SD[sockdes].getpeername()[1])
    Statistics[c_port][2] += byteswritten

    if DEBUG:
        print ("Response Sent")

#----------------------------------------------------------------------------------------------------------------
# Use context manager to free socket resources upon termination
@contextmanager   # Socket Context (resource) manager
def socketcontext(*args, **kwargs):
    sd = socket.socket(*args, **kwargs)
    try:
        yield sd
    finally:
        if DEBUG:
            print ("Listening Socket Closed")
        sd.close()

#----------------------------------------------------------------------------------------------------------------
# Use context manager to free epoll resources upon termination
@contextmanager # epoll loop Context manager
def epollcontext (*args, **kwargs):
    eps = select.epoll()
    eps.register(*args, **kwargs)
    try:
        yield eps
    finally:
        print("\nExiting epoll loop")
        eps.unregister(args[0])
        eps.close()
#----------------------------------------------------------------------------------------------------------------
# Start the epoll server & Process keyboard interrupt CTRL-C
if __name__ == '__main__':
    try:
        EpollServer ([socket.AF_INET, socket.SOCK_STREAM], ("0.0.0.0", ServerPort))
    except KeyboardInterrupt as e:
        for connection in Statistics:
            address, num_req, data_size = Statistics[connection]
            dataQueue.put("%s,%d,%d\n" % (address[0] + ":" + str(address[1]), num_req, data_size))

        dataQueue.put("kill")
        logDataThread.join()

        print("Server Shutdown")
        exit()      # Don't really need this because of context managers
