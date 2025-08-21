from DECK.utils import UTILS

class adterm(UTILS):
    def __init__(self):
        self.cabecalho = ''' IUTE  NOME UTE     LAG  PATAMAR 1   PATAMAR 2   PATAMAR 3
 XXXX  XXXXXXXXXXXX  X  XXXXXXX.XX  XXXXXXX.XX  XXXXXXX.XX'''
        self.campos =[
                (2  , 5 ,"I4*"  , "IUTE"),
                (8  , 19 ,"A11*"  , "NOME"),
                (22  , 22 ,"I1*"  , "LAG"),
                (25  , 34 ,"F10.2*"  , "PAT1"),
                (37  , 46 ,"F10.2*"  , "PAT2"),
                (49  , 58 ,"F10.2*"  , "PAT3"),
                (0,0,"I3*","CODIGO")
            ]
        self.valores = []
        self.endBlock = " 9999\n"

class ADTERM(UTILS):
    def __init__(self,caminho):
        self.blocos = {'adterm':adterm()}
        self.caminho = caminho
        self.adterm = self.blocos['adterm']
        self.nome = "ADTERM"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        codigo = None
        for row in dados[2:]:
            if row.strip().startswith("999"):
                break
            valor = super()._interpretarLinha(self.blocos['adterm'].campos,row)
            if isinstance(valor['IUTE'],int):
                codigo = valor['IUTE']
            else:
                valor['CODIGO'] = codigo
            self.blocos['adterm'].valores.append(valor)

    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    