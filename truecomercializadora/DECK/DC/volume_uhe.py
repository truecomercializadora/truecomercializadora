from DECK.utils import UTILS
from copy import deepcopy
lastDados = {}


class VOLUME(UTILS):
    def __init__(self):
        self.cabecalho = "# ID;VOLUME;TIPO: 0 - altera percentualmente o valor, 1 - aplica o valor percentual de volume, 2 - soma percentualmente ao volume útil"
        self.campos = [
            ( 1 , None ,"I3"  , "ID"),
            ( 2 , None ,"F5.2"  , "VOLUME"),
            ( 3 , None ,"I1"  , "TIPO"),
        ]
        self.valores = []
        self.csv = True
        self.linhaIdentificador = ""


class VOLUME_UHE(UTILS):
    def __init__(self,caminho):
        self.csv = True
        self.blocos = {'VOLUME':VOLUME()}
        self.caminho = caminho
        self.rodape = ["FIM;;"]
        self.nome = "VOLUME UHE"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()



    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()
        for row in dados:
            if row.lower().startswith("fim") or row.lower().startswith("#"): continue
            dadosRow = super()._interpretarLinhaSplitMethod(self.blocos['VOLUME'].campos,row,splitkey=";")
            self.blocos['VOLUME'].valores.append(dadosRow)




    def save(self):
        volumesreferenciaFinal = []
        volumesreferenciaFinal.append(self.blocos['VOLUME'].cabecalho)
        for row in self.blocos['VOLUME'].valores:
            volumesreferenciaFinal.append(";".join([str(x) for x in row.values()]))
        return "\n".join(volumesreferenciaFinal+self.rodape)
    