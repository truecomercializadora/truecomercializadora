from truecomercializadora.DECK.utils import UTILS
from datetime import datetime

class expt_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                        (1 , 4 ,"I4"  , "Cod"),
                        (6 , 10 ,"A5"  , "Tipo"),
                        (12 , 19 ,"F8.2"  , "Valor"),
                        (21 , 22 ,"I2"  , "Mes Inicio"),
                        (24 , 27 ,"I4"  , "Ano Inicio"),
                        (29 , 30 ,"I2*"  , "Mes Fim"),
                        (32 , 35 ,"I4*"  , "Ano Fim"),
                        (38 , 60 ,"A23"  , "Comentario"),
                        (None  , None ,lambda x:self._to_datetime(x["Ano Inicio"],x["Mes Inicio"])  , "DATA_INICIO"),
                        (None  , None ,lambda x:self._to_datetime(x["Ano Fim"],x["Mes Fim"]) , "DATA_FIM"),
                        ]
        self.valores = []
        self.endBlock = ''

class EXPT(UTILS):
    def __init__(self,caminho):
        self.blocos = {'expt':expt_block()}
        self.caminho = caminho
        self.expt = self.blocos['expt']
        self.nome = "EXPT"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['expt'].cabecalho = "\n".join(dados[0:2])
        for row in dados[2:]:
            self.blocos['expt'].valores.append(super()._interpretarLinha(self.blocos['expt'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    