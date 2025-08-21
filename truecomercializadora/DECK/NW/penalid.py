from truecomercializadora.DECK.utils import UTILS

class penalid_block(UTILS):
    def __init__(self):
        self.cabecalho = ''
        self.campos = [
                (2    , 7 ,"A6"  , "PCHAVE"),
                (15  , 22 ,"F8.2" , "Penalidade1"),
                (25   , 32,"F8.2*"  , "Penalidade2"),
                (37   , 39 ,"I3*"  , "Sis"),
                    ]
        self.valores = []

class PENALID(UTILS):
    def __init__(self,caminho):
        self.blocos = {'penalid':penalid_block()}
        self.caminho = caminho
        self.penalid = self.blocos['penalid']
        self.nome = "PENALID"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['penalid'].cabecalho = "\n".join(dados[0:2])
        for row in dados[2:]:
            self.blocos['penalid'].valores.append(super()._interpretarLinha(self.blocos['penalid'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    