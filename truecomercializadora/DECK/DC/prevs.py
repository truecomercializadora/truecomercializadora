from DECK.utils import UTILS


class prevs_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 6 ,"I6"  , "Seq"),    
                ( 7 , 11 ,"I5"  , "Posto"),
                ( 12 , 21 ,"I10"  , "S1"),
                ( 22 , 31 ,"I10"  , "S2"),
                ( 32 , 41 ,"I10"  , "S3"),
                ( 42 , 51 ,"I10"  , "S4"),
                ( 52 , 61 ,"I10"  , "S5"),
                ( 62 , 71 ,"I10"  , "S6"),
                    ]
        self.valores = []

class PREVS(UTILS):
    def __init__(self,caminho):
        self.blocos = {'prevs':prevs_block()}
        self.caminho = caminho
        self.prevs = self.blocos['prevs']
        self.nome = "PREVS" 
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        for row in dados:
            self.blocos['prevs'].valores.append(super()._interpretarLinha(self.blocos['prevs'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    