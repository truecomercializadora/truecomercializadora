from DECK.utils import UTILS

class ree_block(UTILS):
    def __init__(self):
        self.cabecalho = ''
        self.campos =[
                (2  , 4 ,"I3"  , "Numero"),
                (6  , 15 ,"A10"  , "Nome"),
                (19  , 21 ,"I3"  , "Submercado"),
                (24  , 25 ,"I2*"  , "Mes"),
                (27  , 30 ,"I4*"  , "Ano"),
            ]
        self.valores = []
        self.endBlock = " 999"

class fct_block(UTILS):
    def __init__(self):
        self.cabecalho = ''
        self.campos = [
                (1  , 21 ,"A20"  , "Nome"),
                (22  , 26 ,"Z4"  , "Valor"),
                ]
        self.valores = []
        self.endBlock = ''

class REE(UTILS):
    def __init__(self,caminho):
        self.blocos = {'ree':ree_block(), 'fct':fct_block()}
        self.caminho = caminho
        self.ree = self.blocos['ree']
        self.fct = self.blocos['fct']
        self.nome = "REE"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['ree'].cabecalho = "\n".join(dados[0:3])
        bloco = 'ree'
        for row in dados[3:]:
            if row.strip().startswith("999"):
                bloco='fct'
                continue

            if bloco=='ree':
                self.blocos['ree'].valores.append(super()._interpretarLinha(self.blocos['ree'].campos,row))
            else:
                self.blocos['fct'].valores.append(super()._interpretarLinha(self.blocos['fct'].campos,row))

    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    