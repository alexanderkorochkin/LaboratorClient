import sys
sys.path.insert(0, "..")
import time
import socket

from opcua import ua, Server

def get_local_ip():
    return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

if __name__ == "__main__":

    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://" + get_local_ip() + ":4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = server.register_namespace(uri)

    # get Objects node, this is where we should put our nodes
    objects = server.get_objects_node()

    # populating our address space
    myobj = objects.add_object(idx, "MyObject")
    myvar = myobj.add_variable(idx, "MyVariable", 0)
    myvar.set_writable()    # Set MyVariable to be writable by clients

    # starting!
    server.start()
    old_value = 0

    try:
        count = 0
        while True:
            time.sleep(0.1)
            if (myvar.get_value() != old_value):
                print("value = %f" % myvar.get_value())
                old_value = myvar.get_value()
    finally:
        #close connection, remove subcsriptions, etc
        server.stop()