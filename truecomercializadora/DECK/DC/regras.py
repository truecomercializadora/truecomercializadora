from DECK.utils import UTILS


class regras_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' POST   MES  CONF    FORMULA                                                                                                      
 XXXX    XX     X    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'''
        self.campos = [
                (2    , 5 ,"I4"  , "POST"),
                (10   , 12 ,"I2"  , "MES"),
                (16   , 17,"A1"  , "CONF"),
                (21   , 130 ,"A110"  , "FORMULA"),
                    ]
        self.valores = []
        self.endBlock = ' 9999'

class configuracoes_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' CONFIGURACAO DAS REGRAS UTILIZADAS                                                                                           
 POST   2017   2018   2019   2020   2021   2017   2017   2017   2017   2017   2017                                            
 XXXX      X      X      X         '''
        
        self.campos = [
                (2    , 5 ,"I4"  , "POST"),
                (12    , 12 ,"I1" , "A"),
                (19   , 19,"I1*"  , "B"),
                (26   , 26 ,"I1*"  , "C"),
                (33   , 33 ,"I1*"  , "D"),
                (40   , 40 ,"I1*"  , "E"),
                (47   , 47 ,"I1*"  , "F"),
                (54   , 54 ,"I1*"  , "G"),
                (61   , 61 ,"I1*"  , "H"),
                (68   , 68 ,"I1*"  , "I"),
                (75   , 75 ,"I1*"  , "J"),
                (82   , 82 ,"I1*"  , "K"),
                    ]
        self.valores = []
        self.endBlock = ' 9999'

class REGRAS(UTILS):
    def __init__(self,caminho):
        self.blocos = {'regras':regras_block(),'configuracoes':configuracoes_block()}
        self.caminho = caminho
        self.nome = "REGRAS"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        blocoAtual = "regras"
        blocoIniciado = False
        for row in dados:
            if row.strip().startswith("999"):
                blocoAtual = "configuracoes"
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
    