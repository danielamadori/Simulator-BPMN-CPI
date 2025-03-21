from abc import ABC


class Flow:

    def __init__(self, id, srcId, targetId):
        self.id = id
        self.srcId = srcId
        self.targetId = targetId

    def __hash__(self):
        return self.id

    def get_id(self):
        return self.id


class Node(ABC):

    def __init__(self, id, name, label):
        self.id = id
        self.name = name
        self.label = label
        self.create_flows()

    def __hash__(self):
        return self.id

    def create_flows(self):
        self.incoming = []
        self.outgoing = []

    def get_repr_flows(self, flows):
        result = ""

        for flow in flows:
            result += f"\t<bpmn:incoming>{flow.get_id()}</bpmn:incoming>\n"

        return result


# Task
class Task(Node):

    def __repr__(self):
        result = f'<bpmn:task id="{self.id}" name="{self.label}">\n'
        result += self.get_repr_flows(self.incoming)
        result += self.get_repr_flows(self.outgoing)
        result += f"</bpmn:task>"

        return result


# Choice / Nature
class Exclusive(Node):

    def add_div_incoming(self, )

    def create_flows(self):
        self.div_incoming = []
        self.div_outgoing = []
        self.conv_incoming = []
        self.conv_outgoing = []

    def __repr__(self):
        result = f'<bpmn:exclusiveGateway id="enty_{self.id}" name="{self.label}" gatewayDirection="Diverging">\n'

        result += f"</bpmn:exclusiveGateway>\n"

        result = f'<bpmn:exclusiveGateway id="exit_{self.id}" name="{self.label}" gatewayDirection="Converging">\n'

        result += f"</bpmn:exclusiveGateway>"

        return result


# Parallel
class Parallel(Node):
    pass
