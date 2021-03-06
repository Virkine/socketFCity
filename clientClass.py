import synchro_pb2
import socket
import mysql.connector
import sys

import protoFunc
import time
import struct
from sys import stderr


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
        self.HOST = "172.31.3.59"
        self.PORT_CO = 8080
        self.PORT_DECO = 8081

        self.protobufProcess = protoFunc.ProtobufProcessing("Car", "localhost", "root", "root", "fcity")

        #if not self.protobufProcess.detectPause():

        data = synchro_pb2.CarToServ()
        data.connectionRequest.Clear()
        # Create a socket (SOCK_STREAM means a TCP socket)
        self.coSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.coSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            # Connect to server and send data
            self.coSock.connect((self.HOST, self.PORT_CO))
            self.coSock.sendall(data.SerializeToString())

            # Receive data from the server and shut down
            recv = self.coSock.recv(1024)
            self.coSock.close()
         
            msg = synchro_pb2.ServToCar.FromString(recv)
        except Exception as e:
            raise(e)

        print("Sent:     {}".format(data.SerializeToString()))
        print("Received: {}".format(msg.connectionResponse.port))

        self.port = msg.connectionResponse.port
        
        
        # Create a socket (SOCK_STREAM means a TCP socket)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.connect((self.HOST, self.port))

        self.progress = 0

    def synchronize(self):
        try:
            self.protobufProcess.clearDb()

            data = synchro_pb2.CarToServ()
            data.synchronizeRequest.Clear()
            # Connect to server and send data
            data = data.SerializeToString()

            s=struct.pack(">L",len(data))+data
            self.sock.send(s)

            # Receive data from the server and shut down

            bf = self.sock.recv(4)
            sz=struct.unpack(">L",bf)[0]
            recv = recv_message(self.sock, sz)

            # Receive all element of the server database
            self.protobufProcess.protobufElementToDb(recv)
        except Exception as e:
            raise(e)


    def startRide(self) :

        try:    
            msg = self.protobufProcess.startRide()
            s=struct.pack(">L",len(msg))+msg
            self.sock.send(s)

            recv = self.sock.recv(1024)

            if self.protobufProcess.isTaskDone(recv) != True :
                print("The server socket doesnt return response for the start ride")
                sys.exit(1)

        except Exception as e:
            raise(e)

    def setCurrentRide(self,rideId) :
        self.protobufProcess.setCurrentRide(rideId)
    
    def getProgress(self):
        return self.progress

    def endRide(self, endQ):
        try:    
            msg = self.protobufProcess.generateDataMsg()

            self.progress += 1
            endQ.put(self.progress)

            s=struct.pack(">L",len(msg))+msg
            self.sock.send(s)

            self.progress += 1
            endQ.put(self.progress)

            recv = self.sock.recv(1024)

            self.progress += 1
            endQ.put(self.progress)

            if self.protobufProcess.isTaskDone(recv) == True :
                self.sock.close()
                self.progress +=1
                endQ.put(self.progress)

        except Exception as e:
            raise(e)

    def closeSocket(self) :
        try:
            data = synchro_pb2.CarToServ()
            data.endConnectionRequest.port = self.port

            self.decoSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.decoSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.decoSock.connect((self.HOST, self.PORT_DECO))

            self.decoSock.send(data.SerializeToString())
            self.decoSock.close()

            print("End client socket", file=stderr)
        except Exception as e:
            raise(e)

        

