from truecomercializadora.DECK.utils import UTILS
lastDados = {}



class SIMULACAO_FINAL_block(UTILS):
    def __init__(self):
        self.cabecalho = '''   SIMULACAO FINAL:                                                                                                                                   
   X--------X--------X----------------------------------------------------------------------------X----------------------X                            
    ESTAGIO  CENARIO         RESTRICAO VIOLADA                                                           VIOLACAO                                     
   X--------X--------X----------------------------------------------------------------------------X----------------------X    '''
        self.campos = [
                (5  , 12 ,"I7"  , "ESTAGIO"),
                (14  , 21 ,"I7"  , "CENARIO"),
                (23  , 98 ,"A50"  , "RESTRICAO VIOLADA"),
                (100  , 115 ,"F15.8"  , "VIOLACAO"),
                (116  , 121 ,"A5"  , "UNIDADE VIOLACAO"),
                    ]
        self.valores = []
        self.endBlock = ''

class RESTRICOES_block(UTILS):
    def __init__(self):
        self.cabecalho = '''   RELATORIO DE VIOLACOES DAS RESTRICOES OPERATIVAS POR ITERACAO, ESTAGIO E CENARIO:                                                                  
   X---------X--------------X--------X--------X---------------------------------------------------X----------------------X                            
    ITERACAO  FWD(1)/BWD(0)  ESTAGIO  CENARIO      RESTRICAO VIOLADA                                     VIOLACAO                                     
   X---------X--------------X--------X--------X---------------------------------------------------X----------------------X  '''
        self.campos = [
                ( 5 , 13 ,"I8"  , "ITERACAO"),
                ( 15 , 25 ,"I10"  , "FWD(1)/BWD(0)"),
                (30  , 37 ,"I5"  , "ESTAGIO"),
                (39  , 46 ,"I7"  , "CENARIO"),
                (48  , 98 ,"A50"  , "RESTRICAO VIOLADA"),
                (100  , 115 ,"F15.8"  , "VIOLACAO"),
                (116  , 121 ,"A5"  , "UNIDADE VIOLACAO"),
                    ]
        self.valores = []
        self.endBlock = ''


class INVIAB_UNIC(UTILS):
    def __init__(self,caminho):
        self.blocos = {'RESTRICOES':RESTRICOES_block(), 'SIMULACAO_FINAL':SIMULACAO_FINAL_block()}
        self.caminho = caminho
        self.nome = "RELATO"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()
        blocoAtual = ""
        blocoIniciado = False
        ignorarLinhas = 0
        for row in dados:
            if ignorarLinhas>0:
                ignorarLinhas = ignorarLinhas-1
                continue
            if "RELATORIO DE VIOLACOES DAS RESTRICOES OPERATIVAS" in row:
                blocoAtual = "RESTRICOES"
                blocoIniciado = False
                ignorarLinhas = 2
            elif "SIMULACAO FINAL" in row:
                blocoAtual = "SIMULACAO_FINAL"
                blocoIniciado = False
                ignorarLinhas = 2
            elif row.strip().startswith("X-") and blocoAtual!='':
                if not blocoIniciado: blocoIniciado=True
                else:
                    blocoIniciado=False
                    blocoAtual = ""
                continue
            elif row.strip()=='':
                blocoIniciado=False
                blocoAtual = ""


            # print(blocoIniciado,blocoAtual,SEMANA,RELATORIO)
            if blocoIniciado:
                ROW = super()._interpretarLinha(self.blocos[blocoAtual].campos,row)
                self.blocos[blocoAtual].valores.append(ROW)

    def save(self):
        return super()._saveToFile(self.blocos.values())
    