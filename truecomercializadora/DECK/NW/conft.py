from truecomercializadora.DECK.utils import UTILS

class conft_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                        (2    , 5 ,"I4"  , "Num"),
                        (7    , 18 ,"A12" , "Nome"),
                        (22   , 25,"I4"  , "SSis"),
                        (31   , 32 ,"A2"  , "E.Exist"),
                        (36   , 39 ,"I4" , "Classe"),
                        (46   , 48 ,"I3*" , "Tecno"),
                    ]
        self.valores = []
        self.endBlock = ''

class CONFT(UTILS):
    def __init__(self,caminho):
        self.blocos = {'conft':conft_block()}
        self.caminho = caminho
        self.conft = self.blocos['conft']
        self.nome = "CONFT"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['conft'].cabecalho = "\n".join(dados[0:2])
        for row in dados[2:]:
            self.blocos['conft'].valores.append(super()._interpretarLinha(self.blocos['conft'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    