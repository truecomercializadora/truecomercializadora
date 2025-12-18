from truecomercializadora.DECK.utils import UTILS
class FILE(UTILS):
    def __init__(self,caminho):
        self.caminho = caminho
        self.nome = self.caminho.replace("\\","/").rsplit("/",1)[-1].split(".",1)[0] if type(self.caminho)==str else ""
        self.originalBytes = b""
        self.blocos = {}
        self.load()
        self.hash = ""
        self.ERROS = []


    def load(self):
        self.bytes = open
        if type(self.caminho)==bytes:
            self.originalBytes = self.caminho
        else:
            with open(self.caminho, 'rb') as f:
                self.originalBytes = f.read()

    def save(self):
        return self.originalBytes
    