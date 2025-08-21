from truecomercializadora.DECK.utils import UTILS
from copy import deepcopy
lastDados = {}


class patamares_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' NUMERO DE PATAMARES
 XX'''
        self.campos = [
                ( 2 , 3 ,"I2"  , "Patamares"),
                    ]
        self.valores = []




class duracao_block(UTILS):
    def __init__(self):
        self.cabecalho = '''ANO   DURACAO MENSAL DOS PATAMARES DE CARGA
      JAN     FEV     MAR     ABR     MAI     JUN     JUL     AGO     SET     OUT     NOV     DEZ   
      X.XXXX  X.XXXX  X.XXXX  X.XXXX  X.XXXX  X.XXXX  X.XXXX  X.XXXX  X.XXXX  X.XXXX  X.XXXX  X.XXXX'''
        self.campos = [
           (0 , 0 ,"I1*"  , "PATAMAR"),
           (1 , 4 ,"I4*"  , "ANO"),
           (7,  12,"F6.4"  , "1"),
           (15 ,20,"F6.4"  , "2"),
           (23, 28,"F6.4"  , "3"),
           (31, 36,"F6.4"  , "4"),
           (39 ,44,"F6.4"  , "5"),
           (47 ,52,"F6.4"  , "6"),
           (55, 60,"F6.4"  , "7"),
           (63, 68,"F6.4"  , "8"),
           (71 ,76,"F6.4"  , "9"),
           (79 ,84,"F6.4"  , "10"),
           (87, 92,"F6.4"  , "11"),
           (95, 100 ,"F6.4"  , "12"),
                    ]
        self.valores = []




class intercambio_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' SUBSISTEMA
   A ->B
 XXX XXX
                             INTERCAMBIO(P.U.INTERC.MEDIO)
 X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX'''
        self.campos = None
        self.camposList = [
            [
                ( 4 , 7 ,"I4*"  , "Ano"),
                ( 9  , 14,"F6.4"  ,  "1"),
                ( 16 , 21,"F6.4"  ,  "2"),
                ( 23 , 28,"F6.4"  ,  "3"),
                ( 30 , 35,"F6.4"  ,  "4"),
                ( 37 , 42,"F6.4"  ,  "5"),
                ( 44 , 49,"F6.4"  ,  "6"),
                ( 51 , 56,"F6.4"  ,  "7"),
                ( 58 , 63,"F6.4"  ,  "8"),
                ( 65 , 70,"F6.4"  ,  "9"),
                ( 72 , 77,"F6.4"  ,  "10"),
                ( 79 , 84,"F6.4"  ,  "11"),
                ( 86 , 91,"F6.4"  ,  "12"),
                ( 0 , 0 ,"I3*"  , "Submercado A"),
                ( 0 , 0 ,"I3*"  , "Submercado B"),
                ( 0 , 0 ,"I3*"  , "Patamar"),
            ],
            [
                ( 2 , 4 ,"I3"  , "Submercado A"),
                ( 6 , 8 ,"I3"  , "Submercado B"),
                ( 24 , 24 ,"I1*"  , "Flag"),
            ]
        ]
        self.valores = []
        self.endBlock = '9999'



class carga_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' SUBSISTEMA
 XXX
    ANO                       CARGA(P.U.DEMANDA MED.)
   XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX'''
        self.campos = None
        self.camposList = [
            [
                ( 1 , 7 ,"I7*"  , "Ano"),
                ( 9 ,  14 ,"F6.4"  ,  "1"),
                ( 16 , 21 ,"F6.4"  ,  "2"),
                ( 23 , 28 ,"F6.4"  ,  "3"),
                ( 30 , 35 ,"F6.4"  ,  "4"),
                ( 37 , 42 ,"F6.4"  ,  "5"),
                ( 44 , 49 ,"F6.4"  ,  "6"),
                ( 51 , 56 ,"F6.4"  ,  "7"),
                ( 58 , 63 ,"F6.4"  ,  "8"),
                ( 65 , 70 ,"F6.4"  ,  "9"),
                ( 72 , 77 ,"F6.4"  ,  "10"),
                ( 79 , 84 ,"F6.4"  ,  "11"),
                ( 86 , 91 ,"F6.4"  , "12"),
                ( 0 , 0 ,"I3*"  , "Patamar"),
                ( 0 , 0 ,"I3*"  , "Submercado"),
            ],
            [
            ( 2 , 4 ,"I3"  , "Submercado")
            ]
        ]
        
        self.valores = []
        self.endBlock = '9999'



class pequenas_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' SBM  BLOCO
 XXX XXX
    ANO                 BLOCO DE USINAS NAO SIMULADAS (P.U. MONTANTE MED.)
   XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX X.XXXX'''
        self.campos = None
        self.camposList = [
            [
                ( 4 , 7 ,"I4*"  , "Ano"),
                ( 9  , 14,"F6.4"  ,  "1"),
                ( 16 , 21,"F6.4"  ,  "2"),
                ( 23 , 28,"F6.4"  ,  "3"),
                ( 30 , 35,"F6.4"  ,  "4"),
                ( 37 , 42,"F6.4"  ,  "5"),
                ( 44 , 49,"F6.4"  ,  "6"),
                ( 51 , 56,"F6.4"  ,  "7"),
                ( 58 , 63,"F6.4"  ,  "8"),
                ( 65 , 70,"F6.4"  ,  "9"),
                ( 72 , 77,"F6.4"  ,  "10"),
                ( 79 , 84,"F6.4"  ,  "11"),
                ( 86 , 91,"F6.4"  ,  "12"),
                ( 0 , 0 ,"I3*"  , "Submercado"),
                ( 0 , 0 ,"I3*"  , "Tipo"),
                ( 0 , 0 ,"I3*"  , "Patamar"),
            ],
            [
                ( 2 , 4 ,"I3"  , "Submercado"),
                ( 6 , 7 ,"I2"  , "Tipo"),
            ]
        ]
        self.valores = []



class PATAMAR(UTILS):
    def __init__(self,caminho):
        self.blocos = {'patamares':patamares_block(), 'duracao':duracao_block(),'carga':carga_block(), 'intercambio':intercambio_block(), 'pequenas':pequenas_block()}
        self.caminho = caminho
        self.nome = "PATAMAR"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()



    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()
        blocoAtual = ""
        blocoIniciado = False
        for row in dados:
            if "SUBSISTEMA" in row: continue
            if "NUMERO DE PATAMARES" in row:
                blocoAtual = "patamares"
                blocoIniciado = False
            elif "DURACAO MENSAL DOS PATAMARES" in row:
                blocoAtual = "duracao"
                blocoIniciado = False
            elif "CARGA(P.U.DEMANDA MED.)" in row:
                blocoAtual = "carga"
                blocoIniciado = False
            elif "INTERCAMBIO(P.U.INTERC.MEDIO)" in row:
                blocoAtual = "intercambio"
                blocoIniciado = False
            elif "BLOCO DE USINAS NAO SIMULADAS" in row:
                blocoAtual = "pequenas"
                blocoIniciado = False
            elif row.strip().startswith("XXX") or row.strip().startswith("XX") or row.strip().startswith("X.XX"):
                blocoIniciado = True
                continue
            if not blocoIniciado or row.strip().startswith("999"):
                blocoIniciado = False
            if blocoIniciado:
                complementar = True if self.blocos[blocoAtual].campos==None else False

                if complementar:
                    if len(row.split())<3:
                        lastDados = super()._interpretarLinha(self.blocos[blocoAtual].camposList[1],row)
                        lastDados['_indice'] = 1
                        self.blocos[blocoAtual].valores.append(deepcopy(lastDados))
                        lastDados['Patamar'] = 1

                    else:

                        valores = super()._interpretarLinha(self.blocos[blocoAtual].camposList[0],row)
                        if type(valores['Ano'])==int:
                            lastDados['AnoValor'] = valores['Ano']
                        valores.update(lastDados)
                        lastDados['Patamar'] = lastDados['Patamar']+1 if lastDados['Patamar']<3 else 1
                        valores['_indice'] = 0
                        self.blocos[blocoAtual].valores.append(valores)
                else:
                    valores = super()._interpretarLinha(self.blocos[blocoAtual].campos,row)
                    if blocoAtual=='duracao':
                        if type(valores['ANO'])==int:
                            lastAno = valores['ANO']
                            patamar = 1
                        else: patamar+=1
                        valores['AnoValor'] = lastAno
                        valores['PATAMAR'] = patamar
                    self.blocos[blocoAtual].valores.append(valores)

    def save(self):
        return super()._saveToFile(self.blocos.values())
    