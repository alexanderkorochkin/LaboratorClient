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
            print(objects_arr)
            for element in objects_arr:
                print(element.get_browse_name())
                if str(element.get_browse_name()).find("laboratory1") != -1:
                    self.lab_node = element
                    print(str(self.lab_node))
        except Exception:
            raise

    def isConnected(self):
            return self._isConnected

    def Disconnect(self):
        self.disconnect()
        self._isConnected = False


client = OPCUAClient()
