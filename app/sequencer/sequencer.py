import socket
import threading

# Endereço do Sequenciador:
HOST = '127.0.0.1'
PORT = 9000

class Sequenciador:
    def __init__(self):
        self.sequencia_atual = 0
        self.clientes = []
        self.lock = threading.Lock()

    def iniciar(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[SEQUENCIADOR] Rodando em {HOST}:{PORT}...")

        while True:
            conn, addr = server_socket.accept()
            with self.lock:
                self.clientes.append(conn)
            threading.Thread(target=self.tratar_cliente, args=(conn,), daemon=True).start()

    def tratar_cliente(self, conn):
        while True:
            try:
                dados = conn.recv(1024).decode('utf-8')
                if not dados:
                    break
                
                # Formato recebido: "NOME_PROCESSO:Conteudo da mensagem"
                with self.lock:
                    self.sequencia_atual += 1
                    msg_ordenada = f"{self.sequencia_atual}|{dados}"
                    print(f"[SEQUENCIADOR] Atribuído Nº de Sequência {self.sequencia_atual}: '{dados}'")
                    self.multicast(msg_ordenada)

            except Exception:
                break
        
        with self.lock:
            if conn in self.clientes:
                self.clientes.remove(conn)
        conn.close()

    def multicast(self, mensagem):
        """Simula a entrega de multicast enviando para todos os membros ativas do grupo."""
        para_remover = []
        for client in self.clientes:
            try:
                client.sendall((mensagem + "\n").encode('utf-8'))
            except Exception:
                para_remover.append(client)
        
        for c in para_remover:
            self.clientes.remove(c)

if __name__ == '__main__':
    seq = Sequenciador()
    seq.iniciar()
