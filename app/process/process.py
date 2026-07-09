import socket
import threading
import sys

# Endereço do Sequenciador:
HOST = '127.0.0.1'
PORT = 9000

class ProcessoChat:
    def __init__(self, id_processo):
        self.id_processo = id_processo
        self.proxima_sequencia_esperada = 1
        self.buffer_mensagens = {}  # Guarda mensagens fora de ordem: {num_seq: mensagem}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def iniciar(self):
        try:
            self.sock.connect((HOST, PORT))
        except Exception as e:
            print(f"Erro ao conectar ao Sequenciador: {e}")
            return

        print(f"=== Processo Chat [{self.id_processo}] Conectado ===")
        
        # Thread para receber mensagens da rede de forma assíncrona
        t_recebe = threading.Thread(target=self.receber_mensagens, daemon=True)
        t_recebe.start()

        # Thread principal envia as mensagens lidas do teclado
        try:
            while True:
                texto = input()
                if texto.strip().lower() == 'sair':
                    break
                if texto.strip():
                    msg_envio = f"{self.id_processo}:{texto}"
                    self.sock.sendall(msg_envio.encode('utf-8'))
        except KeyboardInterrupt:
            pass
        finally:
            self.sock.close()

    def receber_mensagens(self):
        buffer_socket = ""
        while True:
            try:
                dados = self.sock.recv(1024).decode('utf-8')
                if not dados:
                    break
                buffer_socket += dados
                
                while "\n" in buffer_socket:
                    linha, buffer_socket = buffer_socket.split("\n", 1)
                    if linha:
                        self.processar_mensagem_recebida(linha)
            except Exception:
                break

    def processar_mensagem_recebida(self, pacote):
        # Pacote no formato: "NUMERO_SEQUENCIA|REMETENTE:TEXTO"
        partes = pacote.split("|", 1)
        if len(partes) < 2:
            return
        
        num_seq = int(partes[0])
        conteudo = partes[1]

        # Guarda no buffer local
        self.buffer_mensagens[num_seq] = conteudo

        # Processa as mensagens do buffer em Ordem Total Estrita (1, 2, 3...)
        while self.proxima_sequencia_esperada in self.buffer_mensagens:
            msg_para_exibir = self.buffer_mensagens.pop(self.proxima_sequencia_esperada)
            remetente, txt = msg_para_exibir.split(":", 1)
            
            print(f"[ORDEM TOTAL #{self.proxima_sequencia_esperada}] {remetente}: {txt}")
            self.proxima_sequencia_esperada += 1

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Para rodar um processo: python process.py <NomeDoProcesso>")
        sys.exit(1)

    modo = sys.argv[1]
    if modo:
        proc = ProcessoChat(id_processo=modo)
        proc.iniciar()
