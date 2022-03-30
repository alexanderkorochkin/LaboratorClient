import opcua
from opcua import Client


class OPCUAClient(Client):

    def __init__(self, url="opc.tcp://" + "127.0.0.1" + ":4840", **kwargs):
        super().__init__(url)
        self._isConnected = False
        self._isErr = False
        self.url = ""
        self.root = opcua.Node
        self.myVar = opcua.Node

    def Connect(self):
        try:
            self.connect()
            self._isConnected = True
            self.root = client.get_root_node()
            self.myVar = self.root.get_child(["0:Objects", "2:lab1", "2:MyVariable"])
        except Exception:
            raise

    def isConnected(self):
            return self._isConnected

    def Disconnect(self):
        self.disconnect()
        self._isConnected = False


client = OPCUAClient()
