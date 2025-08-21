from DECK.utils import UTILS

class vazpast_block(UTILS):
    def __init__(self):
        self.cabecalho = ''' POST        USINA       JAN       FEV       MAR       ABR       MAI       JUN       JUL       AGO       SET       OUT       NOV       DEZ
 XXXX XXXXXXXXXXXX XXXXXX.XX XXXXXX.XX XXXXXX.XX XXXXXX.XX XXXXXX.XX XXXXXX.XX XXXXXX.XX XXXXXX.XX XXXXXX.XX XXXXXX.XX XXXXXX.XX XXXXXX.XX
MESPLAN =   {mesplan}     ANOPLAN = {anoplan}'''
        self.campos = [
                (  3,   5,"I3"  , "Numero"),
                (  7,  17,"A11"  , "Nome"),
                ( 20,  28,"F9.2"  , "Jan"),
                ( 30,  38,"F9.2"  , "Fev"),
                ( 40,  48,"F9.2"  , "Mar"),
                ( 50,  58,"F9.2"  , "Abr"),
                ( 60,  68,"F9.2"  , "Mai"),
                ( 70,  78,"F9.2"  , "Jun"),
                ( 80,  88,"F9.2"  , "Jul"),
                ( 90,  98,"F9.2"  , "Ago"),
                (100, 108,"F9.2"  , "Set"),
                (110, 118,"F9.2"  , "Out"),
                (120, 128,"F9.2"  , "Nov"),
                (130, 138,"F9.2"  , "Dez"),
                        ]
        self.valores = []
        self.mesplan = ""
        self.anoplan = ""
        self.endBlock = ''

    def getcabecalho(self):
        return self.cabecalho2.format(mesplan=self.mesplan,anoplan=self.anoplan)
    
class VAZPAST(UTILS):
    def __init__(self,caminho):
        self.blocos = {'vazpast':vazpast_block()}
        self.caminho = caminho
        self.vazpast = self.blocos['vazpast']
        self.nome = "VAZPAST"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()
        self.blocos['vazpast'].mesplan = int(dados[2].split()[2])
        self.blocos['vazpast'].anoplan = int(dados[2].split()[-1])
        for row in dados[3:]:
            self.blocos['vazpast'].valores.append(super()._interpretarLinha(self.blocos['vazpast'].campos,row))
    
    def save(self):
        return super()._saveToFile(self.blocos.values(), {'anoplan':str(self.blocos['vazpast'].anoplan).zfill(4),'mesplan':str(self.blocos['vazpast'].mesplan).rjust(2)})
    