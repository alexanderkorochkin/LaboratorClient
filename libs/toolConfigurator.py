class LabVar:
    def __init__(self, value, index, name, port, multiplier):
        self.isExecuted = True
        self.value = value
        self.index = index
        self.name = name
        self.port = port
        self.multiplier = multiplier
        self.browse_name = ''
        self.node_id = ''

    def isExecuted(self):
        return self.isExecuted


