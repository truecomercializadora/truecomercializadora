from DECK.utils import UTILS


class constante_block(UTILS):
    def __init__(self):
        self.cabecalho = '''VALORES CONSTANTE NO TEMPO
       ALF.x  LBD.x '''
        self.campos = [
                ( 8 , 12 ,"F5.1"  , "Alfa"),
                ( 15 , 19 ,"F5.1"  , "Lambda"),
                    ]
        self.valores = []


class alfa_block(UTILS):
    def __init__(self):
        self.cabecalho = '''VALORES DE ALFA VARIAVEIS NO TEMPO
       JAN.X  FEV.X  MAR.X  ABR.X  MAI.X  JUN.X  JUL.X  AGO.X  SET.X  OUT.X  NOV.X  DEZ.X'''
        
        self.campos = [
            (  1, 5,"A5"  , "Ano"),
            (  8, 12,"F5.1"  ,  "1"),
            ( 15 ,19,"F5.1"  ,  "2"),
            ( 22 ,26,"F5.1"  ,  "3"),
            ( 29 ,33,"F5.1"  ,  "4"),
            ( 36 ,40,"F5.1"  ,  "5"),
            ( 43 ,47,"F5.1"  ,  "6"),
            ( 50 ,54,"F5.1"  ,  "7"),
            ( 57 ,61,"F5.1"  ,  "8"),
            ( 64 ,68,"F5.1"  ,  "9"),
            ( 71 ,75,"F5.1"  ,  "10"),
            ( 78 ,82,"F5.1"  ,  "11"),
            ( 85 ,89,"F5.1"  , "12"),
                    ]
        self.valores = []

class lambda_block(UTILS):
    def __init__(self):
        self.cabecalho = '''VALORES DE LAMBDA VARIAVEIS NO TEMPO
       JAN.X  FEV.X  MAR.X  ABR.X  MAI.X  JUN.X  JUL.X  AGO.X  SET.X  OUT.X  NOV.X  DEZ.X'''
        self.campos = [
            (  1, 5,"A5"  , "Ano"),
            (  8, 12,"F5.1"  ,  "1"),
            ( 15 ,19,"F5.1"  ,  "2"),
            ( 22 ,26,"F5.1"  ,  "3"),
            ( 29 ,33,"F5.1"  ,  "4"),
            ( 36 ,40,"F5.1"  ,  "5"),
            ( 43 ,47,"F5.1"  ,  "6"),
            ( 50 ,54,"F5.1"  ,  "7"),
            ( 57 ,61,"F5.1"  ,  "8"),
            ( 64 ,68,"F5.1"  ,  "9"),
            ( 71 ,75,"F5.1"  ,  "10"),
            ( 78 ,82,"F5.1"  ,  "11"),
            ( 85 ,89,"F5.1"  , "12"),
                ]
        
        self.valores = []
        self.endBlock = ''


class CVAR(UTILS):
    def __init__(self,caminho):
        self.blocos = {'constante':constante_block(),'alfa':alfa_block(),'lambda':lambda_block()}
        self.caminho = caminho
        self.nome = "CVAR"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()

    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()
        blocoAtual = "constante"
        blocoIniciado = False
        for row in dados:
            if "VALORES CONSTANTE" in row:
                blocoAtual = "constante"
                blocoIniciado = False
            elif "VALORES DE ALFA" in row:
                blocoAtual = "alfa"
                blocoIniciado = False
            elif "VALORES DE LAMBDA" in row:
                blocoAtual = "lambda"
                blocoIniciado = False
            elif row.strip().startswith("JAN.X") or row.strip().startswith("ALF.x"):
                blocoIniciado = True
                continue

            if blocoIniciado:
                self.blocos[blocoAtual].valores.append(super()._interpretarLinha(self.blocos[blocoAtual].campos,row))

    
    def save(self):
        return super()._saveToFile(self.blocos.values())
    