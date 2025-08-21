from truecomercializadora.DECK.utils import UTILS



class dger_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                    ( 1 , 21 ,"A21"  , "Descricao"),
                    ( 22, 422 ,"A400"  , "V1"),
                    ]
        self.valores = []
        self.endBlock = ''

class DGER(UTILS):
    def __init__(self,caminho):
        self.blocos = {'dger':dger_block()}
        self.caminho = caminho
        self.dger = self.blocos['dger']
        self.nome = "DGER"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()
        self.blocos['dger'].cabecalho = dados[0]
        for row in dados[1:]:
            self.blocos['dger'].valores.append(super()._interpretarLinha(self.blocos['dger'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    