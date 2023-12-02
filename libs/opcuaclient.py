import threading

from kivy import Logger
from kivy.clock import Clock
from libs.myopcua import Client, ua
from urllib.parse import urlparse

from libs.settings.settingsJSON import msettings
from libs.utils import str_to_variable, timeit

NODE_CLASS_VARIABLE = 2
NODE_CLASS_FOLDER = 1


def name_filter(str_object):
    if isinstance(str_object, ua.uatypes.QualifiedName):
        return str(str_object)[14:-1].split(':')[1]
    return str_object


class OPCUAClient(Client):

    def __init__(self, url="opc.tcp://127.1.1.0"):
        super().__init__(url)
        self.isWaitingSettingValue = None
        self.isUpdatingValues = None
        self._isParsed = False
        self._isConnected = False
        self._isReconnecting = False
        self._isAbort = False
        self.connectWorker = None
        self.disconnectWorker = None
        self.reconnectWorker = None
        self._reconnect_number = 0
        self.timer = None
        self._isErr = False
        self.kivy_instance = None
        self.url = url
        self.root = None
        self.objects = None
        self.lab_node = None
        self.lab_id = ''
        self.names = []
        self.values = []
        self.var_nodes = []
        self.values_stringed_array = []
        self.server_mode = None
        self.out = 'SERVER PARSER OUT:\n'
        self.update_time = None

        self._name_bckp = None
        self._value_bckp = None

    def ParseServerRecursive(self, incoming_node, level=0, ignore_server_node=True, ignore_types_node=True, ignore_views_node=True):

        try:
            _name = name_filter(incoming_node.get_browse_name())
            _class = incoming_node.get_node_class()
        except Exception:
            _name = None
            _class = None
            Logger.debug(f'ParseServerRecursive: Unable to get browse name and node class of incoming node: {incoming_node}')

        if _name and _class:

            def add_decorators(_level):
                _decBranch = ' ┣╍╍'
                _decNormal = ' ┃  '
                if _level == 0:
                    return _decBranch
                else:
                    return _decNormal * _level + _decBranch

            if _class == NODE_CLASS_FOLDER:
                ignored = False
                if ignore_server_node and 'Server' in name_filter(_name):
                    ignored = True
                if ignore_types_node and 'Types' in name_filter(_name):
                    ignored = True
                if ignore_views_node and 'Views' in name_filter(_name):
                    ignored = True
                self.out += add_decorators(level)
                if not ignored:
                    try:
                        childes = incoming_node.get_children()
                        self.out += f' {_name} [{incoming_node}] [type={NODE_CLASS_FOLDER}:FOLDER]\n'
                    except Exception:
                        childes = None
                        self.out += f' {_name} [{incoming_node}] [type={NODE_CLASS_FOLDER}:EMPTY_FOLDER]\n'
                        Logger.debug(f'ParseServerRecursive: Unable to get children of incoming node: {incoming_node}!')
                    if childes:
                        for node in childes:
                            self.ParseServerRecursive(node, level + 1)
                else:
                    self.out += f' ••• skipped: {_name} •••\n'

            # Finding VARIABLES
            elif _class == NODE_CLASS_VARIABLE:

                try:
                    _value = incoming_node.get_value()
                except Exception:
                    _value = 'ERROR'
                    Logger.debug(f'ParseServerRecursive: Unable to get value of incoming node: {incoming_node} from server!')

                self.out += add_decorators(level)

                if isinstance(_value, str):
                    if 'ERROR' in _value:
                        self.out += f' [ERROR in {incoming_node}]\n'
                    elif '\t' in _value:
                        result = _value.split('\n')
                        __names = result[0].split('\t')
                        __values = result[1].split('\t')
                        if len(__names) != len(__values):
                            self.out += f' [BAD UNPACK in {incoming_node}]\n'
                        else:

                            self.values_stringed_array.append([_name, _value])

                            for i in range(len(__names)):
                                __names[i] = __names[i].replace('\r', '')
                            for i in range(len(__values)):
                                __values[i] = str_to_variable(__values[i].replace('\r', ''))

                            self.out += f' {_name} [PACKED] [NodeID: {incoming_node}] [type={NODE_CLASS_VARIABLE}:VARIABLE] [{type(_value).__name__}]\n'

                            for name in __names:
                                self.out += add_decorators(level + 1)
                                self.out += f' {name} [UNPACKED]\n'

                            self.names.extend(list(map(lambda x: f'{_name}::{x}', __names)))
                            self.values.extend(__values)
                            self.var_nodes.extend(list(map(lambda x: incoming_node, __names)))
                    else:
                        self.out += ' [VALUE REPRESENTED AS STRING HASN\'T TABULATION]\n'
                elif isinstance(_value, (float, int, bool)):
                    self.names.append(_name)
                    self.values.append(_value)
                    self.var_nodes.append(incoming_node)

                    self.out += f' {_name} [NodeID: {incoming_node}] [type={NODE_CLASS_VARIABLE}:VARIABLE] [{type(_value).__name__}]\n'
            else:
                self.out += add_decorators(level)
                self.out += f' ••• skipped: {_name} [{_class=}] •••\n'

        return self.out

    def GetValueFromName(self, name):
        if name in self.names:
            return str(self.values[self.names.index(name)])
        else:
            return f'ERROR: Invalid name: {name}'

    def SetValueOnServer(self, _name, _value):
        if self.isUpdatingValues:
            self.isWaitingSettingValue = True
            self._name_bckp = _name
            self._value_bckp = _value
        else:
            if '::' in _name:
                if _name in self.names:
                    out_value = ''
                    for var_name, str_value in self.values_stringed_array:
                        if var_name == _name.split('::')[0]:
                            result = str_value.split('\n')
                            _names = result[0].split('\t')
                            _values = result[1].split('\t')

                            for i in range(len(_names)):
                                if _names[i] == _name.split('::')[1]:
                                    _values[i] = _value

                            for i in range(len(_names)):
                                if i == len(_names) - 1:
                                    out_value += str(_names[i])
                                else:
                                    out_value += str(_names[i]) + '\t'
                            out_value += '\n'
                            for i in range(len(_values)):
                                if i == len(_values) - 1:
                                    out_value += str(_values[i])
                                else:
                                    out_value += str(_values[i]) + '\t'
                    try:
                        if out_value != '':
                            self.values[self.names.index(_name)] = _value
                            self.var_nodes[self.names.index(_name)].set_value(out_value)
                    except Exception:
                        Logger.debug(f'SetValue: Error occurred while setting packed value on server!')

                else:
                    Logger.debug(f'SetValue: No such variable with name: {_name} in names list!')
            else:
                if _name in self.names:
                    try:
                        self.values[self.names.index(_name)] = _value
                        self.var_nodes[self.names.index(_name)].set_value(_value)
                    except Exception:
                        Logger.debug(f'SetValue: Error occurred while setting value on server!')
                else:
                    Logger.debug(f'SetValue: No such variable with name: {_name} in names list!')
            self._name_bckp = None
            self._value_bckp = None

    def UpdateValues(self):
        if not self._isParsed:
            self.ParseLow()
        if self._isConnected and self._isParsed and not self._isReconnecting and not self._isAbort:
            self.isUpdatingValues = True
            i = 0
            updated_vars = []
            self.values_stringed_array = []

            names = self.names
            values = self.values

            for name in names:

                if self._isAbort:
                    return

                if '::' in name:
                    name_parsed = name.split('::')
                    if name_parsed[0] not in updated_vars:
                        try:
                            values_str = self.var_nodes[i].get_value()
                            if values_str:
                                self.values_stringed_array.append([name_parsed[0], values_str])
                                result = values_str.split('\n')
                                _names = result[0].split('\t')
                                _values = result[1].split('\t')
                                if len(_names) != len(_values):
                                    Logger.debug(f'UpdateValues: Bad unpack! Name: {name} NodeID: {self.var_nodes[i]}')
                                else:
                                    for i in range(len(_values)):
                                        _values[i] = str_to_variable(_values[i].replace('\r', ''))
                                    for i in range(len(_names)):
                                        _names[i] = _names[i].replace('\r', '')
                                        _names[i] = f'{name_parsed[0]}::{_names[i]}'
                                        if _names[i] in names:
                                            values[names.index(_names[i])] = _values[i]
                                        else:
                                            Logger.debug(f'UpdateValues: No such variable with name: {_names[i]} in names list!')
                        except Exception:
                            if self._isConnected and not self._isAbort:
                                self.kivy_instance.ConnectionFail(f'UpdateValues: Connection lost!', reconnecting=True)
                                self.ConnectionLost()
                            return
                        updated_vars.append(name_parsed[0])
                else:
                    try:
                        values[i] = self.var_nodes[i].get_value()
                    except Exception:
                        if self._isConnected and not self._isAbort:
                            self.kivy_instance.ConnectionFail(f'UpdateValues: Connection lost!', reconnecting=True)
                            self.ConnectionLost()
                        return
                i += 1

            self.values = values
            self.names = names
            self.update_time = Clock.get_time()
            self.isUpdatingValues = False
            if self.isWaitingSettingValue:
                self.SetValueOnServer(self._name_bckp, self._value_bckp)
                self.isWaitingSettingValue = False
        self.kivy_instance.updateValuesThread = None

    def ConnectLow(self, join=False):
        print(self._isReconnecting, self._isAbort)
        try:
            if not self._isAbort:
                self.connect()
                self._isConnected = True
                self._isReconnecting = False
                if self.reconnectWorker:
                    self.reconnectWorker.cancel()
                    self.reconnectWorker = None
                self.kivy_instance.GoodConnection()
        except Exception:
            if not self._isReconnecting and not self._isAbort:
                self.kivy_instance.ConnectionFail('CONNECT: Failed to connect!')
                self.Disconnect(join)

    def ParseLow(self, join=False):
        if self._isConnected and not self._isAbort:
            try:
                self.names = []
                self.values = []
                self.var_nodes = []
                self.values_stringed_array = []
                self.out = 'SERVER PARSER OUT:\n'
                self.ParseServerRecursive(self.get_root_node())
                Logger.debug(self.out)
                if len(self.names) > 0:
                    self._isParsed = True
                else:
                    self.kivy_instance.ConnectionFail('ParseLow: Empty server!')
                    if not self._isReconnecting:
                        self.Disconnect(join)
            except Exception:
                if not self._isReconnecting:
                    self.kivy_instance.ConnectionFail('ParseLow: Error while parsing server!')
                    self.Disconnect(join)

    def Reconnection(self, i=1):
        if not self._isAbort and not self._isConnected:
            if i <= msettings.get('MAX_RECONNECTIONS_NUMBER'):
                self.Disconnect(join=True)
                self._reconnect_number = i
                Logger.debug(f'CONNECT: Reconnection {i}...')
                self.Connect(join=True)
                if self._isReconnecting:
                    if i == msettings.get('MAX_RECONNECTIONS_NUMBER'):
                        timeout = 0
                    else:
                        timeout = msettings.get('MAX_RECONNECTIONS_NUMBER')
                    self.reconnectWorker = threading.Timer(timeout, self.Reconnection, args=(self._reconnect_number + 1,)).start()
            else:
                self._isAbort = True
                if self.reconnectWorker:
                    self.reconnectWorker.cancel()
                if self.connectWorker:
                    self.connectWorker.cancel()
                self.Disconnect(join=True)
                self.kivy_instance.SetServerState('disconnected')
                self._isReconnecting = False
                self.reconnectWorker = None

    def ConnectionLost(self):
        if msettings.get('DO_RECONNECTION'):
            if not self._isReconnecting:
                self._isReconnecting = True
                self._isConnected = False
                if not self.reconnectWorker:
                    self.reconnectWorker = threading.Timer(msettings.get('RECONNECTION_TIME'), self.Reconnection).start()
        else:
            self._isAbort = True
            self.Disconnect()
            self.kivy_instance.SetServerState('disconnected')
            self._isReconnecting = False

    def ConnectAndParse(self, join=False):
        self.ConnectLow(join)
        self.connectWorker = None

    def Connect(self, url=None, join=False):
        if url:
            self.server_url = urlparse(url)
        self.connectWorker = threading.Thread(target=self.ConnectAndParse, args=(join,)).start()
        if join:
            if self.connectWorker:
                self.connectWorker.join()

    def isParsed(self):
        return self._isParsed

    def isConnected(self):
        return self._isConnected

    def isReconnecting(self):
        return self._isReconnecting

    def Disconnect(self, force=False, join=False):
        self.disconnectWorker = threading.Thread(target=self.DisconnectLow, args=(force,)).start()
        if join:
            if self.disconnectWorker:
                self.disconnectWorker.join()

    def DisconnectLow(self, force=False):
        self.names = []
        self.values = []
        self.var_nodes = []
        self.values_stringed_array = []
        self._isConnected = False
        self._isParsed = False
        self._reconnect_number = 0
        try:
            self.disconnect()
        except Exception:
            pass
        if force:
            self._isAbort = True
            if self.connectWorker:
                self.connectWorker.cancel()
                self.connectWorker = None
            if self.reconnectWorker:
                self.reconnectWorker.cancel()
                self.reconnectWorker = None
            self._isReconnecting = False
            self.kivy_instance.SetServerState('disconnected')
        self.disconnectWorker = None


client = OPCUAClient()
