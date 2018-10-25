from random import randint
import pickle
import socket
import _thread as thread

class Node():

    def __init__(self):
        self.other_nodes = {'app2', 'app3'}
        self.leader = False
        self.candidate = False
        self.value = 0
        self.term = 0
        self.voted = False
        self.log = [('Starting', 1)]
        self.uncommited = []
        self.listen()


    def listen(self):
        self.timeout = randint(150, 300)
        socket.setdefaulttimeout(3)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('', 8000))
        self.server.listen()

        while True:
            #accept connections from outside
            try:
                (clientsocket, address) = self.server.accept()
                message = clientsocket.recv(1024)
                message_type, value = pickle.loads(message)

                if message_type == 'Heartbeat':
                    print('Hearbeat recieved')
                    self.log = value
                    self.uncommited = []
                    self.candidate = False
                    self.server.settimeout(3)

                elif message_type == 'Request votes':
                    new_term = value
                    if self.term != new_term:
                        print('Voting')
                        self.term = new_term
                        try:
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect((address[0], 8001))
                            message = ('1', self.term)
                            s.send(pickle.dumps(message))
                            s.close()
                        except ConnectionRefusedError:
                            pass

            except socket.timeout:
                print('Timeout reached')
                if not self.leader:
                    self.candidate = True
                    thread.start_new_thread(self.ask_votes, tuple())
                else:
                    self.send_heartbeat()

    def send_heartbeat(self):
        print('Sending heartbeat')
        for node in self.other_nodes:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host_ip = socket.gethostbyname(node)
            s.connect((host_ip, 8000))
            message = ('Heartbeat', self.log)
            s.send(pickle.dumps(message))
            s.close()

    def ask_votes(self):
        print('Asking for votes')
        self.term += 1

        votes = 1
        vote_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        vote_listen.bind(('', 8001))
        vote_listen.listen()

        for node in self.other_nodes:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host_ip = socket.gethostbyname(node)
            s.connect((host_ip, 8000))
            message = ('Request votes', self.term)
            s.send(pickle.dumps(message))
            s.close()

        while votes <= len(self.other_nodes)//2 and self.candidate:
            try:
                (clientsocket, address) = vote_listen.accept()
            except socket.timeout:
                break
            vote, term = pickle.loads(clientsocket.recv(1024))
            if vote == '1' and term == self.term:
                votes += 1

        vote_listen.close()

        if votes > len(self.other_nodes)//2:
            print('Elected. Becoming leader')
            self.leader = True
            self.candidate = False
            self.server.settimeout(1)

Node()
