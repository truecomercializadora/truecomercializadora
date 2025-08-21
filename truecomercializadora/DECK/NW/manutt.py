from truecomercializadora.DECK.utils import UTILS
from datetime import datetime,timedelta

class manutt_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2  ,"I2"  , "CodEmpresa"),
                ( 3 , 13 ,"A11"  , "Empresa"),
                (18 , 20 ,"I3"  , "Cod"),
                (21 , 33 ,"A13"  , "Usina"),
                (38 , 39 ,"I2"  , "Unidade"),
                (40 , 40 ,"A1"  , "T"),
                (41 , 42 ,"Z2"  , "Dia"),
                (43 , 44 ,"Z2"  , "Mes"),
                (45 , 48 ,"Z4"  , "Ano"),
                (50 , 52 ,"I3"  , "Duracao"),
                (56 , 62 ,"F7.2"  , "Potencia"),
                (None  , None ,lambda x:self._to_datetime(x["Ano"],x["Mes"],x['Dia'])  , "DATA_INICIO"),
                (None,None, lambda x:x["DATA_INICIO"]+timedelta(days=x["Duracao"]-1), 'DATA_FIM'),
                (None,None,lambda x:self._contar_dias_por_mes(x["DATA_INICIO"],x["DATA_FIM"]),"DIAS_MES"),
        ]
        self.valores = []
        self.endBlock = ''

class MANUTT(UTILS):
    def __init__(self,caminho):
        self.blocos = {'manutt':manutt_block()}
        self.caminho = caminho
        self.manutt = self.blocos['manutt']
        self.nome = "MANUTT"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['manutt'].cabecalho = "\n".join(dados[0:2])
        for row in dados[2:]:
            self.blocos['manutt'].valores.append(super()._interpretarLinha(self.blocos['manutt'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
        
