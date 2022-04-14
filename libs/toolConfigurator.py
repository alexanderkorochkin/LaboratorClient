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
        if len(self.values_history) <= MAX_HISTORY_VALUES:
            self.values_history.append(_value)
        else:
            del self.values_history[0]
            self.values_history.append(_value)
