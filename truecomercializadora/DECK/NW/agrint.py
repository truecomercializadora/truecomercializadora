from truecomercializadora.DECK.utils import UTILS
from datetime import datetime

class agrupamento_block(UTILS):
    def __init__(self):
        self.cabecalho = '''AGRUPAMENTOS DE INTERCÂMBIO
 #AG A   B   COEF
 XXX XXX XXX XX.XXXX'''
        self.campos = [
                (2  , 4 ,"I3"  , "Numero"),
                (6  , 8,"I3"  ,  "A"),
                (10  ,12 ,"I3"  , "B"),
                (14  ,20 ,"F7.4"  , "Coef"),
                    ]
        self.valores = []
        self.endBlock = ' 999'

class detalhes_block(UTILS):
    def __init__(self):
        self.cabecalho = '''LIMITES POR GRUPO
  #AG MI ANOI MF ANOF LIM_P1  LIM_P2  LIM_P3
 XXX  XX XXXX XX XXXX XXXXXX. XXXXXX. XXXXXX.'''
        
        self.campos = [
                (2  , 4 ,  "I3"  , "Numero"),
                (7  , 8 ,  "I2"  ,  "Mes Ini"),
                (10  ,13 , "I4"  , "Ano Ini"),
                (15  ,16 , "I2*"  , "Mes Fim"),
                (18  ,21 , "I4*"  , "Ano Fim"),
                (23  ,29 , "F7.0."  , "ValorP1"),
                (31  ,37 , "F7.0."  , "ValorP2"),
                (39  ,45 , "F7.0."  , "ValorP3"),
                (50  ,100 ,"A51"  , "Descricao"),
                (None  , None ,lambda x:self._to_datetime(x["Ano Ini"],x["Mes Ini"])  , "DATA_INICIO"),
                (None  , None ,lambda x:self._to_datetime(x["Ano Fim"],x["Mes Fim"]) , "DATA_FIM"),
                    ]
        self.valores = []
        self.endBlock = ' 999\n'

class AGRINT(UTILS):
    def __init__(self,caminho):
        self.blocos = {'agrupamentos':agrupamento_block(),'detalhes':detalhes_block()}
        self.caminho = caminho
        self.nome = "AGRINT"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        blocoAtual = ""
        blocoIniciado = False
        for row in dados:
            if "AGRUPAMENTOS DE INTERCÂMBIO" in row:
                blocoAtual = "agrupamentos"
                blocoIniciado = False
            elif "LIMITES POR GRUPO" in row:
                blocoAtual = "detalhes"
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
    