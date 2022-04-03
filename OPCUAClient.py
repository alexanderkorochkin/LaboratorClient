import opcua
from opcua import Client
from urllib.parse import urlparse


class OPCUAClient(Client):

    def __init__(self, url="opc.tcp://127.0.0.1", **kwargs):
        super().__init__(url)
        self._isConnected = False
        self._isErr = False
        self.url = url
        self.root = opcua.Node
        self.objects = opcua.Node

    def Connect(self, url):
        try:
            self.server_url = urlparse(url)
            self.connect()
            self._isConnected = True
            self.root = self.get_root_node()
        except Exception:
            raise

    def isConnected(self):
            return self._isConnected

    def Disconnect(self):
        self.disconnect()
        self._isConnected = False

client = OPCUAClient()

