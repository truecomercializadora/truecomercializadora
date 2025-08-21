from truecomercializadora.DECK.utils import UTILS
from copy import deepcopy
lastDados = {}


class patamares_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' PATAMAR DE DEFICIT
 NUMERO DE PATAMARES DE DEFICIT
 XXX'''
        self.campos = [
                        ( 2 , 4 ,"I3"  , "Patamares")
                    ]
        self.valores = []




class deficit_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' CUSTO DO DEFICIT
 NUM|NOME SSIS.|    CUSTO DE DEFICIT POR PATAMAR  | P.U. CORTE POR PATAMAR|
 XXX|XXXXXXXXXX| F|XXXX.XX XXXX.XX XXXX.XX XXXX.XX|X.XXX X.XXX X.XXX X.XXX|'''
        self.campos = [
                ( 2 , 4 ,"I3"  , "Num"),
                ( 6 , 15 ,"A10"  , "Submercado"),
                ( 18 , 18 ,"I1"  , "F"),
                ( 20 , 26 ,"F7.2*"  , "Custo 1"),
                ( 28 , 34 ,"F7.2*"  , "Custo 2"),
                ( 36 , 42 ,"F7.2*"  , "Custo 3"),
                ( 44 , 50 ,"F7.2*"  , "Custo 4"),
                ( 52 , 56 ,"F5.3*"  , "PU 1"),
                ( 58 , 62 ,"F5.3*"  , "PU 2"),
                ( 64 , 68 ,"F5.3*"  , "PU 3"),
                ( 70 , 74 ,"F5.3*"  , "PU 4")
                    ]
        self.valores = []
        self.endBlock = ' 999'




class intercambio_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' LIMITES DE INTERCAMBIO
 A   B   A->B    B->A
 XXX XXX XJAN. XXXFEV. XXXMAR. XXXABR. XXXMAI. XXXJUN. XXXJUL. XXXAGO. XXXSET. XXXOUT. XXXNOV. XXXDEZ.'''
        self.campos = None
        self.camposList = [
            [
                ( 1 , 4 ,"I4*"  , "Ano"),
                ( 8 ,  14 ,"F7.0.*"  ,  "Limite Mes 1"),
                ( 16 , 22 ,"F7.0.*"  ,  "Limite Mes 2"),
                ( 24 , 30 ,"F7.0.*"  ,  "Limite Mes 3"),
                ( 32 , 38 ,"F7.0.*"  ,  "Limite Mes 4"),
                ( 40 , 46 ,"F7.0.*"  ,  "Limite Mes 5"),
                ( 48 , 54 ,"F7.0.*"  ,  "Limite Mes 6"),
                ( 56 , 62 ,"F7.0.*"  ,  "Limite Mes 7"),
                ( 64 , 70 ,"F7.0.*"  ,  "Limite Mes 8"),
                ( 72 , 78 ,"F7.0.*"  ,  "Limite Mes 9"),
                ( 80 , 86 ,"F7.0.*"  ,  "Limite Mes 10"),
                ( 88 , 94 ,"F7.0.*"  ,  "Limite Mes 11"),
                ( 96 , 102 ,"F7.0."  , "Limite Mes 12"),
                ( 0 , 0 ,"I3*"  , "Submercado A"),
                ( 0 , 0 ,"I3*"  , "Submercado B"),
            ],
            [
                ( 2 , 4 ,"I3"  , "Submercado A"),
                ( 6 , 8 ,"I3"  , "Submercado B"),
                ( 24 , 24 ,"I1"  , "Flag"),
            ]
        ]
        self.valores = []
        self.endBlock = ' 999'



class mercado_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' MERCADO DE ENERGIA TOTAL
 XXX
       XXXJAN. XXXFEV. XXXMAR. XXXABR. XXXMAI. XXXJUN. XXXJUL. XXXAGO. XXXSET. XXXOUT. XXXNOV. XXXDEZ.'''
        self.campos = None
        self.camposList = [
            [
                ( 1 , 4 ,"I4**"  , "Ano"),
                ( 8 ,  14 ,"F7.0.*"  ,  "1"),
                ( 16 , 22 ,"F7.0.*"  ,  "2"),
                ( 24 , 30 ,"F7.0.*"  ,  "3"),
                ( 32 , 38 ,"F7.0.*"  ,  "4"),
                ( 40 , 46 ,"F7.0.*"  ,  "5"),
                ( 48 , 54 ,"F7.0.*"  ,  "6"),
                ( 56 , 62 ,"F7.0.*"  ,  "7"),
                ( 64 , 70 ,"F7.0.*"  ,  "8"),
                ( 72 , 78 ,"F7.0.*"  ,  "9"),
                ( 80 , 86 ,"F7.0.*"  ,  "10"),
                ( 88 , 94 ,"F7.0.*"  ,  "11"),
                ( 96 , 102 ,"F7.0."  , "12"),
                ( 0 , 0 ,"I3*"  , "Submercado"),
            ],
            [
            ( 2 , 4 ,"I3"  , "Submercado")
            ]
        ]
        
        self.valores = []
        self.endBlock = ' 999'



class pequenas_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' GERACAO DE USINAS NAO SIMULADAS
 XXX  XBL  XXXXXXXXXXXXXXXXXXXX  XTE
       XXXJAN. XXXFEV. XXXMAR. XXXABR. XXXMAI. XXXJUN. XXXJUL. XXXAGO. XXXSET. XXXOUT. XXXNOV. XXXDEZ.'''
        self.campos = None
        self.camposList = [
            [
                ( 1 , 4 ,"I4*"  , "Ano"),
                ( 8 ,  14 ,"F7.0.*"  ,  "1"),
                ( 16 , 22 ,"F7.0.*"  ,  "2"),
                ( 24 , 30 ,"F7.0.*"  ,  "3"),
                ( 32 , 38 ,"F7.0.*"  ,  "4"),
                ( 40 , 46 ,"F7.0.*"  ,  "5"),
                ( 48 , 54 ,"F7.0.*"  ,  "6"),
                ( 56 , 62 ,"F7.0.*"  ,  "7"),
                ( 64 , 70 ,"F7.0.*"  ,  "8"),
                ( 72 , 78 ,"F7.0.*"  ,  "9"),
                ( 80 , 86 ,"F7.0.*"  ,  "10"),
                ( 88 , 94 ,"F7.0.*"  ,  "11"),
                ( 96 , 102 ,"F7.0."  , "12"),
                ( 0 , 0 ,"I3*"  , "Submercado"),
                ( 0 , 0 ,"I3*"  , "Tipo"),
                ( 0 , 0 ,"A9*"  , "Descricao"),
            ],
            [
                ( 2 , 4 ,"I3"  , "Submercado"),
                ( 7 , 9 ,"I3"  , "Tipo"),
                ( 12 , 20 ,"A9"  , "Descricao"),
            ]
        ]
        self.valores = []
        self.endBlock = ' 999\n'



class SISTEMA(UTILS):
    def __init__(self,caminho):
        self.blocos = {'patamares':patamares_block(),'deficit':deficit_block(), 'intercambio':intercambio_block(), 'mercado':mercado_block(), 'pequenas':pequenas_block()}
        self.caminho = caminho
        self.nome = "SISTEMA"
        self.ERROS = []
        self.load()
        self.patamares = self.blocos['patamares']
        self.deficit = self.blocos['deficit']
        self.intercambio = self.blocos['intercambio']
        self.mercado = self.blocos['mercado']
        self.pequenas = self.blocos['pequenas']
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()
        blocoAtual = ""
        blocoIniciado = False
        for row in dados:
            if "PATAMAR DE DEFICIT" in row:
                blocoAtual = "patamares"
                blocoIniciado = False
            elif "CUSTO DO DEFICIT" in row:
                blocoAtual = "deficit"
                blocoIniciado = False
            elif "LIMITES DE INTERCAMBIO" in row:
                blocoAtual = "intercambio"
                blocoIniciado = False
            elif "MERCADO DE ENERGIA TOTAL" in row:
                blocoAtual = "mercado"
                blocoIniciado = False
            elif "GERACAO DE PEQUENAS USINAS" in row or "GERACAO DE USINAS NAO SIMULADAS" in row:
                blocoAtual = "pequenas"
                blocoIniciado = False
            elif row.strip().startswith("XXX"):
                blocoIniciado = True
                continue
            if not blocoIniciado or row.strip().startswith("999"):
                blocoIniciado = False
            if blocoIniciado:
                complementar = True if self.blocos[blocoAtual].campos==None else False

                if complementar:
                    if row.startswith("   "):
                        lastDados = super()._interpretarLinha(self.blocos[blocoAtual].camposList[1],row)
                        lastDados['_indice'] = 1
                        self.blocos[blocoAtual].valores.append(deepcopy(lastDados))
                    elif len(row.strip())==0 and blocoAtual=="intercambio":
                        A,B = lastDados['Submercado A'],lastDados['Submercado B']
                        lastDados['Submercado A'] = B
                        lastDados['Submercado B'] = A
                        lastDados['_indice'] = 1
                        self.blocos[blocoAtual].valores.append({'Submercado A':'','Submercado B':"",'Flag':""})
                    else:
                        valores = super()._interpretarLinha(self.blocos[blocoAtual].camposList[0],row)
                        valores.update(lastDados)
                        valores['_indice'] = 0
                        self.blocos[blocoAtual].valores.append(valores)
                else:
                    self.blocos[blocoAtual].valores.append(super()._interpretarLinha(self.blocos[blocoAtual].campos,row))

    def save(self):
        return super()._saveToFile(self.blocos.values())
    