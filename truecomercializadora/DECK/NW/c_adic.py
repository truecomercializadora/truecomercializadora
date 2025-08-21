from truecomercializadora.DECK.utils import UTILS
from copy import deepcopy
lastDados = {}



class c_adic_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = None
        self.camposList = [
            [
                ( 1 , 4 ,"A4"  , "Ano"),
                ( 8 ,  14 ,"F7.0.*"  ,  "1"),
                ( 16 , 22 ,"F7.0.*"  ,  "2"),
                ( 24 , 30 ,"F7.0.*"  ,  "3"),
                ( 32 , 38 ,"F7.0.*"  ,  "4"),
                ( 40 , 46 ,"F7.0.*"  ,  "5"),
                ( 48 , 54 ,"F7.0.*"  ,  "6"),
                ( 56 , 62 ,"F7.0.*"  ,  "7"),
                ( 64 , 70 ,"F7.0.*"  ,  "8"),
                ( 72 , 78 ,"F7.0.*"  ,  "9"),
                ( 80 , 86 ,"F7.0.*"  ,  "10"),
                ( 88 , 94 ,"F7.0.*"  ,  "11"),
                ( 96 , 102 ,"F7.0.*"  , "12"),
                ( 0 , 0,"I*"  , "Submercado"),
                ( 0 , 0,"A*"  , "Texto"),
            ],
            [
                ( 2 , 4 ,"I3"  , "Submercado"),
                ( 6 , 32 ,"A27"  , "Texto"),
            ]
        ]
        
        self.valores = []
        self.endBlock = ' 999\n'



class C_ADIC(UTILS):
    def __init__(self,caminho):
        self.blocos = {'c_adic':c_adic_block()}
        self.caminho = caminho
        self.nome = "C_ADIC"
        self.ERROS = []
        self.load()
        self.c_adic = self.blocos['c_adic']
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()
        self.blocos['c_adic'].cabecalho = "\n".join(dados[0:2])
        for row in dados[2:]:
            if row.startswith("   "):
                lastDados = super()._interpretarLinha(self.blocos['c_adic'].camposList[1],row)
                lastDados['_indice'] = 1
                self.blocos['c_adic'].valores.append(deepcopy(lastDados))
            elif row.startswith(" 999"): continue
            else:
                valores = super()._interpretarLinha(self.blocos['c_adic'].camposList[0],row)
                valores.update(lastDados)
                valores['_indice'] = 0
                self.blocos['c_adic'].valores.append(valores)


    def save(self):
        return super()._saveToFile(self.blocos.values())
    