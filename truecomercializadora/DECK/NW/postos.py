from DECK.utils import UTILS

class postos_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
            (  0, 0, "I*", "Cod"),
            (1 ,12 ,"A12","Posto"),
            (13,16,"I4","InicioHistorico"),
            (17,20,"I4","FinalHistorico"),
                    ]
        self.valores = []
        self.size = 20

class POSTOS(UTILS):
    def __init__(self,caminho):
        self.blocos = {'postos':postos_block()}
        self.caminho = caminho
        self.postos = self.blocos['postos']
        self.nome = "POSTOS"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        if type(self.caminho)==bytes:
            dados = self.caminho
        else:
            with open(self.caminho, 'rb') as f:
                dados = f.read()

        for i in range(len(dados) // self.blocos['postos'].size):
            reg_bytes = dados[self.blocos['postos'].size * i:self.blocos['postos'].size * (i + 1)]
            dadosLinha = super()._interpretarLinhaBinaria(self.blocos['postos'].campos,reg_bytes,{"Cod":i+1})
            self.blocos['postos'].valores.append(dadosLinha)
    
    def save(self):
        return super()._saveToFileBytes(self.blocos.values())
    