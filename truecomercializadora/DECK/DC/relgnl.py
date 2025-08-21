from truecomercializadora.DECK.utils import UTILS
from datetime import datetime
lastDados = {}




class COMANDOS_block(UTILS):
    def __init__(self):
        self.cabecalho = '''   X---X-----------X---X------X-----------X----------X----------X----------X
                                             pat 1      pat 2      pat 3
    Num   Usina     Lag Subsis   Semana    (MWmed)    (MWmed)    (MWmed)   
   X---X-----------X---X------X-----------X----------X----------X----------X'''
        self.campos = [
                ( 4 , 8 ,"I4"  , "Cod"),
                ( 9 , 19 ,"A10"  , "Usina"),
                ( 21 , 23 ,"I3"  , "Lag"),
                ( 25 , 30 ,"A5"  , "Subsis"),
                ( 32 , 42 ,"A10"  , "Semana"),
                ( 44 , 54 ,"F10.2"  , "MWmed Pat1"),
                ( 55 , 65 ,"F10.2"  , "MWmed Pat2"),
                ( 66 , 76 ,"F10.2"  , "MWmed Pat3"),
                (None,None, lambda x:datetime.strptime(x['Semana'].strip(),"%d/%m/%Y"),"DATA")
                    ]
        self.valores = []
        self.endBlock = ' 999'

class CENARIOS_block(UTILS):
    def __init__(self):
        self.cabecalho = '''   X---X-----------X-------X-------X--------X-------X--------X-------X--------X-------X----------X------------X
    Sis    Usina     Lag(k)               pat_1            pat_2            pat_3        Custo    Inic semana
                     meses  Semana   (MWmed)  Dur(h)  (MWmed)  Dur(h)  (MWmed)  Dur(h)  (1000 $)  (dd/mm/aaaa)
   X---X-----------X-------X-------X--------X-------X--------X-------X--------X-------X----------X------------X'''
        self.campos = [
                ( 4 , 7 ,"A3"  , "Sis"),
                ( 9 , 19 ,"A10"  , "Usina"),
                ( 21 , 27 ,"I6"  , "Lag"),
                ( 29 , 35 ,"A6"  , "Semana"),
                ( 37 , 44 ,"F7.2"  , "MWmed Pat1"),
                ( 46 , 52 ,"F6.2"  , "Dur Pat1"),
                ( 54 , 61 ,"F7.2"  , "MWmed Pat2"),
                ( 63 , 69 ,"F6.2"  , "Dur Pat2"),
                ( 71 , 78 ,"F7.2"  , "MWmed Pat3"),
                ( 80 , 86 ,"F6.2"  , "Dur Pat3"),
                ( 88 , 97 ,"F9.1"  , "Custo"),
                ( 99 , 110 ,"A11"  , "Inic semana"),
                (None,None, lambda x:datetime.strptime(x['Inic semana'].strip(),"%d/%m/%Y"),"DATA"),
                (0,0,"I2","ESTAGIO"),
                (0,0,"I2","SEMANA"),
                (0,0,"I2","CENARIO"),
                    ]
        self.valores = []
        self.endBlock = ' 999'

class LAG_block(UTILS):
    def __init__(self):
        self.cabecalho = '''   X---X-----------X-----X
    Num   Usina      Lag  
   X---X-----------X-----X'''
        self.campos = [
                ( 4 , 8 ,"I4"  , "Cod"),
                ( 9 , 19 ,"A10"  , "Usina"),
                ( 21 , 25 ,"I5"  , "Lag"),  
                    ]
        self.valores = []
        self.endBlock = ' 999'


class RELGNL(UTILS):
    def __init__(self,caminho):
        self.blocos = {'COMANDOS':COMANDOS_block(),"LAG":LAG_block(),"CENARIOS":CENARIOS_block()}
        self.caminho = caminho
        self.nome = "RELGNL"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()
        blocoAtual = ""
        blocoIniciado = False
        ignorarLinhas = 0
        relatorio = False
        SEMANA=None
        ESTAGIO=None
        for row in dados:
            if ignorarLinhas>0:
                ignorarLinhas = ignorarLinhas-1
                continue
            if "Relatorio dos comandos das usinas GNL com possiveis ajustes devido a registros TG" in row:
                blocoAtual = "COMANDOS"
                blocoIniciado = False
                ignorarLinhas = 2
            elif "Lags de antecipacao de despacho para cada usina GNL (registros NL)" in row:
                blocoAtual = "LAG"
                blocoIniciado = False
                ignorarLinhas = 2
            elif "RELATORIO  DA  OPERACAO  TERMICA E CONTRATOS" in row:
                relatorio = True
            elif relatorio and "SEMANA" in row and "- ESTAGIO" in row:
                SEMANA = int(row.split("SEMANA",1)[-1].split("-",1)[0])
                ESTAGIO = int(row.split("ESTAGIO",1)[-1].split("/",1)[0])
                CENARIO = int(row.split("CENARIO",1)[-1].split("-",1)[0])
            elif "Sinalizacao de Despacho antecipado em k meses" in row:
                blocoAtual = "CENARIOS"
                blocoIniciado = False
                ignorarLinhas = 3

            elif row.strip().startswith("X-") and blocoAtual!='':
                if not blocoIniciado: blocoIniciado=True
                else:
                    blocoIniciado=False
                    blocoAtual = ""
                continue
            elif row.strip()=="":
                blocoIniciado=False
                blocoAtual = ""


            # print(blocoIniciado,blocoAtual,SEMANA,RELATORIO)
            if blocoIniciado:
                ROW = super()._interpretarLinha(self.blocos[blocoAtual].campos,row)
                if blocoAtual=='CENARIOS':
                    ROW['ESTAGIO'] = ESTAGIO
                    ROW['SEMANA'] = SEMANA
                    ROW['CENARIO'] = CENARIO
                self.blocos[blocoAtual].valores.append(ROW)

    def save(self):
        return super()._saveToFile(self.blocos.values())
    