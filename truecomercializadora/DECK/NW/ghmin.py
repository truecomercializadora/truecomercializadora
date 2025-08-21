from DECK.utils import UTILS

class ghmin_block(UTILS):
    def __init__(self):
        self.cabecalho = ''
        self.campos = [
                (1 , 3 ,"I3"  , "Cod"),
                (6 , 7 ,"I2"  , "Mes"),
                (9 , 12 ,"A4"  , "Ano"),
                (15, 15 ,"I1"  , "Patamar"),
                (18 , 23 ,"F5.1"  , "Potencia"),
                    ]
        self.valores = []
        self.endBlock = '999\n'

class GHMIN(UTILS):
    def __init__(self,caminho):
        self.blocos = {'ghmin':ghmin_block()}
        self.caminho = caminho
        self.ghmin = self.blocos['ghmin']
        self.nome = "GHMIN"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['ghmin'].cabecalho = "\n".join(dados[0:2])
        for row in dados[2:]:
            if row.strip().startswith("999"): continue
            self.blocos['ghmin'].valores.append(super()._interpretarLinha(self.blocos['ghmin'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    