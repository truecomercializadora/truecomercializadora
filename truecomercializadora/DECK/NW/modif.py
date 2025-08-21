from truecomercializadora.DECK.utils import UTILS
from datetime import datetime
        
class modif_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos=None
        self.camposList = [
                [ #USINA LINE
                    ( 2 , 7 ,"A6"  , "Tipo"),
                    (11  , 14 ,"i3"  , "Usina"),
                    (45  , 90 ,"A50"  , "COMENTARIO"),
                ],
                [ #DEFAULT LINE
                    (2 , 9 ,"A8"  , "Tipo"),
                    (11  , 18 ,"A7"  , "Valor1"),
                    (19  , 25 ,"A7"  , "Valor2"),
                    (26  , 44 ,"A19"  , "Valor3"),
                    (45  , 90 ,"A50"  , "COMENTARIO"),
                ],
                [#VMAXT LINE *
                    (2 , 9 ,"A8"  , "Tipo"),
                    (11  , 12 ,"I2"  , "MES"),
                    (14  , 18 ,"I4"  , "ANO"),
                    (19  , 25 ,"F7.3"  , "Valor"),
                    (27  , 31 ,"A5"  , "Unidade"),
                    (None  , None ,lambda x:self._to_datetime(x["ANO"],x["MES"])  , "DATA"),
                ],
                [ #CMONT LINE
                    (2 , 9 ,"A8"  , "Tipo"),
                    (11  , 12 ,"I2"  , "MES"),
                    (14  , 18 ,"I4"  , "ANO"),
                    (19  , 25 ,"F7.2"  , "Valor"),
                    (26  , 31 ,"A6"  , "Unidade"),
                    (None  , None ,lambda x:self._to_datetime(x["ANO"],x["MES"])  , "DATA"),
                ],
                [ #VAZMIN LINE
                    (2 , 9 ,"A8"  , "Tipo"),
                    (12  , 17 ,"F5.0"  , "Valor"),
                ],
                [ #TURBMAXT LINE
                    (2 , 9 ,"A8"  , "Tipo"),
                    (11  , 12 ,"I2"  , "MES"),
                    (14  , 17 ,"I4"  , "ANO"),
                    (19  , 25 ,"F7.2"  , "Valor"),
                    (None  , None ,lambda x:self._to_datetime(x["ANO"],x["MES"])  , "DATA"),
                ],
                [ #TURBMINT Line
                    (2 , 9 ,"A8"  , "Tipo"),
                    (11  , 12 ,"I2"  , "MES"),
                    (14  , 17 ,"I4"  , "ANO"),
                    (18  , 25 ,"F7.2"  , "Valor"),
                    (None  , None ,lambda x:self._to_datetime(x["ANO"],x["MES"])  , "DATA"),
                ],
                [ #VMINT Line
                    (2 , 9 ,"A8"  , "Tipo"),
                    (11  , 12 ,"I2"  , "MES"),
                    (14  , 17 ,"I4"  , "ANO"),
                    (19  , 25 ,"F7.3"  , "Valor"),
                    (27  , 31 ,"A5"  , "Unidade"),
                    (None  , None ,lambda x:self._to_datetime(x["ANO"],x["MES"])  , "DATA"),
                ],
                [ #VAZMINT Line
                    (2 , 9 ,"A8"  , "Tipo"),
                    (11  , 12 ,"I2"  , "MES"),
                    (14  , 18 ,"I4"  , "ANO"),
                    (19  , 25 ,"F7.2"  , "Valor"),
                    (None  , None ,lambda x:self._to_datetime(x["ANO"],x["MES"])  , "DATA"),
                ],
                [ #CMONT LINE
                    (2 , 9 ,"A8"  , "Tipo"),
                    (11  , 12 ,"I2"  , "MES"),
                    (14  , 18 ,"I4"  , "ANO"),
                    (19  , 25 ,"F7.2"  , "Valor"),
                    (26  , 31 ,"A6"  , "Unidade"),
                    (None  , None ,lambda x:self._to_datetime(x["ANO"],x["MES"])  , "DATA"),
                ],
                [ #VOLMIN LINE
                    (2 , 9 ,"A8"  , "Tipo"),
                    (11  , 25 ,"F15.2"  , "Valor"),
                    (27  , 31 ,"A6"  , "Unidade"),
                ],

        ]
        self.valores = []
        self.endBlock = ''

class MODIF(UTILS):
    def __init__(self,caminho):
        self.blocos = {'modif':modif_block()}
        self.caminho = caminho
        self.modif = self.blocos['modif']
        self.nome = "MODIF"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['modif'].cabecalho = "\n".join(dados[0:2])
        lastUsina = 0
        
        for row in dados[2:]:
            if "USINA" in row:
                valores = super()._interpretarLinhaSplitMethod(self.blocos['modif'].camposList[0],row)
                valores['_indice'] = 0
                self.blocos['modif'].valores.append(valores)
                lastUsina = valores['Usina']

            else:
                valores = {}
                A = False
                if 'VMAXT' in row:
                    valores = super()._interpretarLinhaSplitMethod(self.blocos['modif'].camposList[2],row)
                    valores['_indice'] = 2
                    A = True
                elif 'CMONT' in row:
                    valores = super()._interpretarLinhaSplitMethod(self.blocos['modif'].camposList[3],row)
                    valores['_indice'] = 3
                    A = True
                elif 'TURBMAXT' in row:
                    valores = super()._interpretarLinhaSplitMethod(self.blocos['modif'].camposList[5],row)
                    valores['_indice'] = 5
                    A = True
                elif 'VMINT' in row:
                    valores = super()._interpretarLinhaSplitMethod(self.blocos['modif'].camposList[7],row)
                    valores['_indice'] = 7
                    A = True
                elif 'VAZMINT' in row:
                    valores = super()._interpretarLinhaSplitMethod(self.blocos['modif'].camposList[8],row)
                    valores['_indice'] = 8
                    A = True
                elif 'TURBMINT' in row:
                    valores = super()._interpretarLinhaSplitMethod(self.blocos['modif'].camposList[6],row)
                    valores['_indice'] = 6
                    A = True
                elif 'VAZMIN' in row:
                    valores = super()._interpretarLinhaSplitMethod(self.blocos['modif'].camposList[4],row)
                    valores['_indice'] = 4
                    A = True
                elif 'CFUGA' in row:
                    valores = super()._interpretarLinhaSplitMethod(self.blocos['modif'].camposList[9],row)
                    valores['_indice'] = 9
                    A = True
                elif 'VOLMIN' in row or 'VOLMAX' in row:
                    valores = super()._interpretarLinhaSplitMethod(self.blocos['modif'].camposList[10],row)
                    valores['_indice'] = 10
                    A = True
                elif not A:
                    valores = super()._interpretarLinha(self.blocos['modif'].camposList[1],row)
                    valores['_indice'] = 1
                valores['Usina'] = lastUsina
                self.blocos['modif'].valores.append(valores)

    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    