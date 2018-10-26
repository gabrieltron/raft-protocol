import time
import socket
import pickle

nodes = {'app1', 'app2', 'app3'}

while True:
    time.sleep(15)
    print('Woke up! Time to tell the cluster to add 3!')
    # Since we don't know which node is the leader, send to everyone.
    # Everyone but the leader will ignore it
    for node in nodes:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host_ip = socket.gethostbyname(node)
        s.connect((host_ip, 8002))
        message = 'Add 3'
        s.send(pickle.dumps(message))
        s.close()