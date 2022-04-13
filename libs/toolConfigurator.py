import kivy
from kivy.logger import Logger


class LabVar:
    def __init__(self, value, index, name, port, multiplier):
        self.isExecuted = True
        self.value = value
        self.index = index
        self.name = name
        self.port = port
        self.multiplier = multiplier

    def isExecuted(self):
        return self.isExecuted

    def GetValue(self):
        return self.value

    def GetIndex(self):
        return self.index

    def GetName(self):
        return self.name

    def GetPort(self):
        return self.port

    def GetMultiplier(self):
        return self.multiplier

    def SetValue(self, value):
        self.value = value

    def SetIndex(self, index):
        self.index = index

    def SetName(self, name):
        self.name = name

    def SetPort(self, port):
        self.port = port

    def SetMultiplier(self, multiplier):
        self.multiplier = multiplier


def Configure(path):
    arr = []
    file = open(path, "r")
    for line in file:
        index, port, name, *multiplier = line.split("\t", 4)
        arr.append(LabVar(0, index, name, port, multiplier))
    file.close()
    return arr
