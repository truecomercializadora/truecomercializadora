from truecomercializadora.DECK.utils import UTILS


class confhd_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                (2    , 5 ,"I4"  , "Cod"),
                (7    , 18 ,"A12" , "Usina"),
                (20    ,23 ,"I4"  , "Posto"),
                (26   , 29,"I4"  , "CodJusante"),
                (31   , 34,"I4"  , "REE"),
                (36   , 41 ,"F6.2"  , "Vol Util"),
                (45   , 46 ,"A2" , "Situacao"),
                (50   , 53,"I4"  , "Modif"),
                (59   , 62,"I4"  , "Inicio Hidr"),
                (68   , 71,"I4"  , "Fim Hidr"),
                (74   , 76,"I3*"  , "Tecno"),
                    ]
        self.valores = []
        self.endBlock = ''

class CONFHD(UTILS):
    def __init__(self,caminho):
        self.blocos = {'confhd':confhd_block()}
        self.caminho = caminho
        self.confhd = self.blocos['confhd']
        self.nome = "CONFHD"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['confhd'].cabecalho = "\n".join(dados[0:2])
        for row in dados[2:]:
            self.blocos['confhd'].valores.append(super()._interpretarLinha(self.blocos['confhd'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    