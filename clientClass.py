import synchro_pb2
import socket
import mysql.connector
import sys

import testProto
import time
import struct

def recv_message(connection,sz):
        data = list()
        transferred_bytes= 0
        while transferred_bytes < sz:
            data.append(connection.recv(min(sz-transferred_bytes, 2048)))
            if not data[-1]:
                raise RuntimeError("socket connection broken")
            transferred_bytes += len(data[-1])
        return b''.join(data)

class ClientSocket :
    def __init__(self):
        protobufProcess = testProto.ProtobufProcessing("Car", "localhost", "root", "root", "fcity")

        protobufProcess.clearDb()

        HOST, PORT = "172.17.3.241", 8080
        data = synchro_pb2.CarToServ()
        data.connectionRequest.Clear()
        # Create a socket (SOCK_STREAM means a TCP socket)
        fSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        fSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            # Connect to server and send data
            fSock.connect((HOST, PORT))
            fSock.sendall(data.SerializeToString())

            # Receive data from the server and shut down
            recv = fSock.recv(1024)
         
            msg = synchro_pb2.ServToCar.FromString(recv)
        except Exception as e:
            raise(e)

        print("Sent:     {}".format(data.SerializeToString()))
        print("Received: {}".format(msg.connectionResponse.port))

        PORT = msg.connectionResponse.port
        
        
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE,1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

    def startRide(self) :
        try:
	    data = synchro_pb2.CarToServ()
            data.synchronizeRequest.Clear()
            # Connect to server and send data
            data = data.SerializeToString()

            sock.connect((HOST, PORT))
            s=struct.pack(">L",len(data))+data
            sock.send(s)

            # Receive data from the server and shut down
            
            bf = sock.recv(4)
            sz=struct.unpack(">L",bf)[0]
            recv = recv_message(sock, sz)

            # Receive all element of the server database
            protobufProcess.protobufElementToDb(recv)

        except Exception as e:
            raise(e)

    def getCurrentRide(self) :
        if protobufProcess.setCurrentRide() == -1 :
            print("No ride has been booked")
            return -1
        else :
            return protobufProcess.setCurrentRide()

    def endRide(self):
        try:    
            s=struct.pack(">L",len(msg))+msg
            sock.send(s)

            recv = sock.recv(1024)

            if protobufProcess.isTaskDone(recv) != True :
                print("The server socket doesnt return response for the start ride")
                sys.exit(1)

            msg = protobufProcess.generateData()

            s=struct.pack(">L",len(msg))+msg
            sock.send(s)

            recv = sock.recv(1024)

            if protobufProcess.isTaskDone(recv) == True :
                sock.close()

        except Exception as e:
            raise(e)

        print("Sent:     {}".format(data))
        print("Received: {}".format(recv))

        data = synchro_pb2.CarToServ()
        data.endConnectionRequest.Clear()

        try :
            fSock.send(data.SerializeToString())
        except Exception as e:
            raise(e)
        finally :
            fSock.close()

