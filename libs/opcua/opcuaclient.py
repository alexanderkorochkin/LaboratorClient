import opcua
from opcua import Client
from urllib.parse import urlparse
from libs.variables import LabVar
from libs.settings.settingsJSON import msettings


class OPCUAClient(Client):

    def __init__(self, url="opc.tcp://127.0.0.1"):
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

    def GetVarsFromNode(self):
        arr = []
        for child in self.lab_node.get_children():
            ch = client.get_node(child)
            if ch.get_node_class() == 2:
                arr.append(LabVar(str(ch.get_browse_name())[str(ch.get_browse_name()).find(":") + 1:len(str(ch.get_browse_name())) - 1]))
        return arr

    def Connect(self, url):
        try:
            self.server_url = urlparse(url)
            self.connect()
            self._isConnected = True
            self.root = self.get_root_node()
            self.objects = self.get_objects_node()
            objects_arr = self.objects.get_children()
            for element in objects_arr:
                if str(element.get_browse_name()).find(msettings.get('NAMESPACE')) != -1:
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
