from DECK.utils import UTILS



class term_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                        (2    , 4 ,"I3"  , "Cod"),
                        (6    , 17 ,"A12" , "Usina"),
                        (20   ,  24 ,"F5.0."  , "Potencia"),
                        (26   ,  29 ,"F4.0."  , "FCMX"),
                        (32   ,  37 ,"F6.2"  , "TEIF"),
                        (39   ,  44 ,"F6.2"  , "IP"),
                        (46   ,  51 ,"F6.2"  , "GTMIN1"),
                        (53   ,  58 ,"F6.2"  , "GTMIN2"),
                        (60   ,  65 ,"F6.2"  , "GTMIN3"),
                        (67   ,  72 ,"F6.2"  , "GTMIN4"),
                        (74   ,  79 ,"F6.2"  , "GTMIN5"),
                        (81   ,  86 ,"F6.2"  , "GTMIN6"),
                        (88   ,  93 ,"F6.2"  , "GTMIN7"),
                        (95   ,  100 ,"F6.2"  , "GTMIN8"),
                        (102  ,   107 ,"F6.2"  , "GTMIN9"),
                        (109  ,   114 ,"F6.2"  , "GTMIN10"),
                        (116  ,   121 ,"F6.2"  , "GTMIN11"),
                        (123  ,   128 ,"F6.2"  , "GTMIN12"),
                        (130  ,   135 ,"F6.2"  , "GTMIN D+ ANOS"),
                    ]
        self.valores = []
        self.endBlock = ''

class TERM(UTILS):
    def __init__(self,caminho):
        self.blocos = {'term':term_block()}
        self.caminho = caminho
        self.term = self.blocos['term']
        self.nome = "TERM"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['term'].cabecalho = "\n".join(dados[0:2])
        for row in dados[2:]:
            self.blocos['term'].valores.append(super()._interpretarLinha(self.blocos['term'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    