import opcua
from opcua import Client
from urllib.parse import urlparse
from settings.config import *


class OPCUAClient(Client):

    def __init__(self, url="opc.tcp://127.0.0.1", **kwargs):
        super().__init__(url)
        self._isConnected = False
        self._isReconnecting = False
        self._reconnect_number = 0
        self._isErr = False
        self.url = url
        self.root = opcua.Node
        self.objects = opcua.Node
        self.lab_node = opcua.Node
        self.lab_id = ''

    def Connect(self, url):
        try:
            self.server_url = urlparse(url)
            self.connect()
            self._isConnected = True
            self.root = self.get_root_node()
            self.objects = self.get_objects_node()
            objects_arr = self.objects.get_children()
            for element in objects_arr:
                if str(element.get_browse_name()).find(NAMESPACE) != -1:
                    self.lab_node = element
        except Exception:
            raise

    def isConnected(self):
        return self._isConnected

    def isReconnecting(self):
        return self._isReconnecting

    def GetReconnectNumber(self):
        return self._reconnect_number

    def ReconnectNumberInc(self):
        self._reconnect_number += 1

    def ReconnectNumberZero(self):
        self._reconnect_number = 0

    def Disconnect(self):
        try:
            self.disconnect()
            self._isConnected = False
        except Exception:
            self._isConnected = False


client = OPCUAClient()
