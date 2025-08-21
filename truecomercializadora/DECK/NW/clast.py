from DECK.utils import UTILS
from datetime import datetime

class conjunturais_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' NUM     CUSTO
 XXXX   XXXX.XX  XX XXXX  XX XXXX'''
        self.campos = [
                (2    , 5 ,"I4"  , "Num"),
                (9   , 15 ,"F7.2"  , "CVU"),
                (18   , 19,"I2*"  , "Mes Inicio"),
                (21   , 24 ,"I4*"  , "Ano Inicio"),
                (27   , 28 ,"I2*"  , "Mes Fim"),
                (30   , 33 ,"I4*"  , "Ano Fim"),
                (36   , 47 ,"A12" , "Nome"),
                (None  , None ,lambda x:self._to_datetime(x["Ano Inicio"],x["Mes Inicio"])  , "DATA_INICIO"),
                (None  , None ,lambda x:self._to_datetime(x["Ano Fim"],x["Mes Fim"]) , "DATA_FIM"),

                    ]
        self.valores = []
        self.endBlock = ''

class estruturais_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' NUM  NOME CLASSE  TIPO COMB.  CUSTO   CUSTO   CUSTO   CUSTO   CUSTO   
 XXXX XXXXXXXXXXXX XXXXXXXXXX XXXX.XX XXXX.XX XXXX.XX XXXX.XX XXXX.XX'''
        
        self.campos = [
                (2    , 5 ,"I4"  , "Num"),
                (7    , 18 ,"A12" , "Nome"),
                (20   , 29,"A10"  , "Combustivel"),
                (31   , 37 ,"F7.2"  , "CVU1"),
                (39   , 45 ,"F7.2"  , "CVU2"),
                (47   , 53 ,"F7.2"  , "CVU3"),
                (55   , 61 ,"F7.2"  , "CVU4"),
                (63   , 69 ,"F7.2"  , "CVU5"),
                    ]
        self.valores = []
        self.endBlock = ' 9999'

class CLAST(UTILS):
    def __init__(self,caminho):
        self.blocos = {'estruturais':estruturais_block(),'conjunturais':conjunturais_block()}
        self.caminho = caminho
        self.nome = "CLAST"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        blocoAtual = "estruturais"
        blocoIniciado = True
        self.blocos['estruturais'].cabecalho = "\n".join(dados[0:2])
        for row in dados[2:]:
            if row.strip().startswith("999"):
                blocoAtual = "conjunturais"
                blocoIniciado = False
            elif row.strip().startswith("XXX"):
                blocoIniciado = True
                continue
            if not blocoIniciado or row.strip().startswith("999"):
                blocoIniciado = False

            if blocoIniciado:
                self.blocos[blocoAtual].valores.append(super()._interpretarLinha(self.blocos[blocoAtual].campos,row))

    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    