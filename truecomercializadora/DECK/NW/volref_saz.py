from truecomercializadora.DECK.utils import UTILS


class volref_saz_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 3 ,"I3"  , "Num"),
                ( 5 , 17 ,"A12"  , "Nome"),                
                (20  , 28 ,"F8.2"  , "1"),
                (30  , 38 ,"F8.2"  , "2"),
                (40  , 48 ,"F8.2"  , "3"),
                (50  , 58 ,"F8.2"  , "4"),
                (60  , 68,"F8.2"  , "5"),
                (70  , 78 ,"F8.2"  , "6"),
                (80  , 88 ,"F8.2"  , "7"),
                (90  , 98,"F8.2"  , "8"),
                (100  , 108,"F8.2"  , "9"),
                (110  , 118,"F8.2"  , "10"),
                (120  , 128,"F8.2"  , "11"),
                (130  , 140,"F8.2"  , "12"),
                    ]
        self.valores = []

class VOLREF_SAZ(UTILS):
    def __init__(self,caminho):
        self.blocos = {'volref_saz':volref_saz_block()}
        self.caminho = caminho
        self.volref_saz = self.blocos['volref_saz']
        self.nome = "VOLREF_SAZ"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        self.blocos['volref_saz'].cabecalho = "\n".join(dados[0:3])
        for row in dados[3:]:
            self.blocos['volref_saz'].valores.append(super()._interpretarLinha(self.blocos['volref_saz'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    