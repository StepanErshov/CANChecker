from pyvis.network import Network

net = Network()
net.add_node(1, label="Node A")
net.add_node(2, label="Node B")
net.add_edge(1, 2)
net.show("graph.html", notebook=False)