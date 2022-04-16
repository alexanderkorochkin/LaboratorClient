from settings.config import *


class LabVar:
    def __init__(self, value, index, name, port, multiplier):
        self.isExecuted = True
        self.value = value
        self.values_history = []
        self.index = index
        self.name = name
        self.port = port
        self.multiplier = multiplier
        self.browse_name = ''
        self.node_id = ''

    def isExecuted(self):
        return self.isExecuted

    def WriteHistory(self, _value):
        if len(self.values_history) < MAX_HISTORY_VALUES:
            self.values_history.append([len(self.values_history), _value])
        else:
            for i in range(len(self.values_history)):
                if i < (len(self.values_history) - 1):
                    self.values_history[i][1] = self.values_history[i + 1][1]
                    self.values_history[i][0] += 1
                else:
                    self.values_history[i][1] = float(_value)
                    self.values_history[i][0] += 1

    def GetHistory(self):
        return self.values_history

    def ClearHistory(self):
        self.values_history = []
