from truecomercializadora.DECK.utils import UTILS


class dsvagua_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 4 ,"I4"  , "Ano"),
                ( 6 , 9 ,"I4"  , "Usina"),                
                (10  , 16 ,"F7.2"  , "1"),
                (17  , 23 ,"F7.2"  , "2"),
                (24  , 30 ,"F7.2"  , "3"),
                (31  , 37 ,"F7.2"  , "4"),
                (38  , 44 ,"F7.2"  , "5"),
                (45  , 51 ,"F7.2"  , "6"),
                (52  , 58 ,"F7.2"  , "7"),
                (59  , 65,"F7.2"  , "8"),
                (66  , 72,"F7.2"  , "9"),
                (73  , 79,"F7.2"  , "10"),
                (80  , 86,"F7.2"  , "11"),
                (87  , 93,"F7.2"  , "12"),
                (98  , 101,"i4"  , "Consi NC"),
                (102 , 151,"A50"  , "Descricao"),
                    ]
        self.valores = []
        self.endBlock = '9999\n'

class DSVAGUA(UTILS):
    def __init__(self,caminho):
        self.blocos = {'dsvagua':dsvagua_block()}
        self.caminho = caminho
        self.dsvagua = self.blocos['dsvagua']
        self.nome = "DSVAGUA"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['dsvagua'].cabecalho = "\n".join(dados[0:2])
        for row in dados[2:]:
            if row.strip().startswith("999"): continue

            self.blocos['dsvagua'].valores.append(super()._interpretarLinha(self.blocos['dsvagua'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    