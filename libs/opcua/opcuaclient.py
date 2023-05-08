import opcua
from kivy import Logger
from opcua import Client, ua
from urllib.parse import urlparse

from libs.utils import str_to_variable

NODE_CLASS_VARIABLE = 2
NODE_CLASS_FOLDER = 1


def name_filter(str_object):
    if isinstance(str_object, opcua.ua.uatypes.QualifiedName):
        return str(str_object)[14:-1].split(':')[1]
    return str_object


class OPCUAClient(Client):

    def __init__(self, url="opc.tcp://127.1.1.0"):
        super().__init__(url)
        self._isConnected = False
        self._isReconnecting = False
        self._reconnect_number = 0
        self._isErr = False
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

    def UpdateValues(self):
        i = 0
        updated_vars = []
        self.values_stringed_array = []
        for name in self.names:
            if '::' in name:
                name_parsed = name.split('::')
                if name_parsed[0] not in updated_vars:
                    values_str = self.var_nodes[i].get_value()
                    if values_str:
                        self.values_stringed_array.append([name_parsed[0], values_str])
                        result = values_str.split('\n')
                        _names = result[0].split('\t')
                        _values = result[1].split('\t')
                        if len(_names) != len(_values):
                            Logger.debug(f'UpdateValues: Bad unpack! Name: {name} NodeID: {self.var_nodes[i]}')
                        else:
                            for i in range(len(_names)):
                                _names[i] = _names[i].replace('\r', '')
                            __names = list(map(lambda x: f'{name_parsed[0]}::{x}', _names))
                            for i in range(len(_values)):
                                _values[i] = str_to_variable(_values[i].replace('\r', ''))

                            for i in range(len(__names)):
                                if __names[i] in self.names:
                                    self.values[self.names.index(__names[i])] = _values[i]
                                else:
                                    Logger.debug(f'UpdateValues: No such variable with name: {__names[i]} in names list!')
                    updated_vars.append(name_parsed[0])
            else:
                self.values[i] = self.var_nodes[i].get_value()
            i += 1

    def Connect(self, url):
        self.server_url = urlparse(url)
        self.connect()
        self._isConnected = True

        self.names = []
        self.values = []
        self.var_nodes = []
        self.values_stringed_array = []
        self.out = 'SERVER PARSER OUT:\n'
        Logger.debug(self.ParseServerRecursive(self.get_root_node()))
        return 0

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
