from truecomercializadora.DECK.utils import UTILS


class penalizacao_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' XXX XXX XXX      (TIPO DE PENALIZACAO: 0-FIXA 1-MAXPEN; MES PENALIZACAO: 1 A 12;  VMINOP SAZONAL NO PRE/POS: 0-NAO CONSIDERA 1-CONSIDERA)'''
        self.campos = [
            (  2 ,5, "Z3"  , "Tipo"),
            (  6 ,8, "Z3"  ,  "Mes"),
            ( 10 ,13,"Z3"  ,  "VMINOP"),
                    ]
        self.valores = []


class custo_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' SISTEMA   CUSTO
 XXX       XXXX.XX'''
        
        self.campos = [
                ( 2 , 4 ,"Z3"  , "Ree"),
                (12 ,18 ,"F5.2"  , "Custo"),
                    ]
        self.valores = []
        self.endBlock = ' 999'

class curva_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' CURVA DE SEGURANCA (EM % DE EARMX)
 XXX
      JAN.X FEV.X MAR.X ABR.X MAI.X JUN.X JUL.X AGO.X SET.X OUT.X NOV.X DEZ.X'''
        self.campos = None
        self.camposList = [
                [
                    (  1 ,4, "I4"  , "Ano"),
                    (  7 ,12,"F5.1"  ,  "Mes 1"),
                    ( 13 ,18,"F5.1"  ,  "Mes 2"),
                    ( 19 ,24,"F5.1"  ,  "Mes 3"),
                    ( 25 ,30,"F5.1"  ,  "Mes 4"),
                    ( 31 ,36,"F5.1"  ,  "Mes 5"),
                    ( 37 ,42,"F5.1"  ,  "Mes 6"),
                    ( 43 ,48,"F5.1"  ,  "Mes 7"),
                    ( 49 ,54,"F5.1"  ,  "Mes 8"),
                    ( 55 ,60,"F5.1"  ,  "Mes 9"),
                    ( 61 ,66,"F5.1"  ,  "Mes 10"),
                    ( 67 ,72,"F5.1"  ,  "Mes 11"),
                    ( 73 , 78,"F6.1"  , "Mes 12"),
                    ( 0 , 0 ,"I3*"  , "Ree"),
                ],
                [
                    (  1 ,4, "I4"  , "Ree"),
                ]
        ]
                
        self.valores = []
        self.endBlock = '9999'



class CURVA(UTILS):
    def __init__(self,caminho):
        self.blocos = {'penalizacao':penalizacao_block(),'custo':custo_block(),'curva':curva_block()}
        self.caminho = caminho
        self.nome = "CURVA"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()
        self.rodape = '''
PROCESSO ITERATIVO DA ETAPA 2 DO MECANISMO DE AVERSAO AO RISCO
NUM. MAXIMO DE ITERACOES         0     (SE = 0 -> NAO USA PROC. ITERATIVO DA ETAPA 2)
ITERACAO A PARTIR               10
TOLERANCIA P/ PROCESSO       0.010     (EM % DA PENALIDADE DE REFERENCIA)
IMPRESSAO DE RELATORIO           0     (=0 NAO IMPRIME; =1 IMPRIME)
'''

    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        blocoAtual = "penalizacao"
        blocoIniciado = False
        for row in dados:
            if "CUSTO" in row:
                blocoAtual = "custo"
                blocoIniciado = False
            elif "CURVA" in row:
                blocoAtual = "curva"
                blocoIniciado = False
            elif row.strip().startswith("XXX") or row.strip().startswith("JAN.X"):
                blocoIniciado = True
                continue
            if not blocoIniciado or row.strip().startswith("999"):
                blocoIniciado = False

            if blocoIniciado:
                if self.blocos[blocoAtual].campos==None:
                    if len(row.strip())<=2:
                        lastvalor = super()._interpretarLinha(self.blocos[blocoAtual].camposList[1],row)
                        lastvalor['_indice'] = 1
                        self.blocos[blocoAtual].valores.append(lastvalor)
                    else:
                        valores = super()._interpretarLinha(self.blocos[blocoAtual].camposList[0],row)
                        valores.update(lastvalor)
                        valores['_indice'] = 0
                        self.blocos[blocoAtual].valores.append(valores)


                else:
                    self.blocos[blocoAtual].valores.append(super()._interpretarLinha(self.blocos[blocoAtual].campos,row))

    
    def save(self):
        return super()._saveToFile(self.blocos.values()) + self.rodape.encode("latin-1")
    