from truecomercializadora.DECK.utils import UTILS
from copy import deepcopy
lastDados = {}
from truecomercializadora.DECK.DC.dadger import ac, rhq, rhe, rhv, hecm

class TG(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
            (1 , 2 ,"A2"   ,"Id" ),
            (5 , 7 ,"I3"   ,"Usina" ),
            (10 ,11,"I2"   ,"Subsistema" ),
            (15 ,24,"A10"  ,"Nome" ),
            (25 ,26,"I2"   ,"Estagio" ),
            (30 ,34,"F5.1" ,"Ger Min Pat1" ),
            (35 ,39,"F5.1" ,"Capacidade Pat1" ),
            (40 ,49,"F10.2","CVU Pat1" ),
            (50 ,54,"F5.1" ,"Ger Min Pat2" ),
            (55 ,59,"F5.1" ,"Capacidade Pat2" ),
            (60 ,69,"F10.2","CVU Pat2" ),
            (70 ,74,"F5.1" ,"Ger Min Pat3" ),
            (75 ,79,"F5.1" ,"Capacidade Pat3" ),
            (80 ,89,"F10.2","CVU Pat3" )
            ]
        self.valores = []

class GS(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
            (1  , 2 ,"A2"    , "Id"),
            (5  , 6 ,"I2"    , "Mes"),
            (10  , 10 ,"I1"    , "Intervalos"),
            ]
        self.valores = []

class NL(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                (1 , 2 ,"A2"   ,"Id" ),
                (5 , 7 ,"I3"   ,"Usina" ),
                (10 ,11,"I2"   ,"Subsistema" ),
                (15 ,15,"I1"   ,"Lag" ),
                ]
        self.valores = []

class GL(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [(1  , 2 ,"A2"    , "Id"),
                    (5  , 7 ,"I3"    , "Usina"),                
                    (10 , 11,"I2"    , "Subsistema"),
                    (15 , 16,"I2"    , "Semana"),
                    (20 , 29,"F10.1" , "Geracao Pat1"),
                    (30 , 34,"F5.1*"  , "Duracao Pat1"),
                    (35 , 44,"F10.1" , "Geracao Pat2"),
                    (45 , 49,"F5.1*"  , "Duracao Pat2"),
                    (50 , 59,"F10.1" , "Geracao Pat3"),
                    (60 , 64,"F5.1*"  , "Duracao Pat3"),
                    (66 , 67,"Z2"    , "Dia inicio"),
                    (68 , 69,"Z2"    , "Mes inicio"),
                    (70 , 73,"Z4"    , "Ano inicio"),
                    ]
        self.valores = []

class NaoMapeado_block:
    def __init__(self):
        self.cabecalho = ""
        self.campos = []
        self.valores = []

class DADGNL(UTILS):
    def __init__(self,caminho):
        super().__init__()  # Chama o __init__ da classe base
        self.blocos = {}
        self.caminho = caminho
        self.blocosMapeados = {'TG':TG(), 'GS':GS(), 'NL':NL(), 'GL':GL()}
        self.rodape = []
        self.nome = "DADGNL"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        comentarios = []
        for row in dados:
                if row.startswith("&") or len(row.strip())==0:
                    comentarios.append(row)
                else:
                    cod = row[0:2]
                    if (cod == ""): continue
                    CHECK = next((x for x in self.blocosMapeados.keys() if cod in x.split()), False)
                    if CHECK:
                        if CHECK not in self.blocos.keys():
                            self.blocos[CHECK] = self.blocosMapeados[CHECK]
                        bloco = self.blocos[CHECK]
                    else:
                        CHECK = next((x for x in self.blocos.keys() if cod in x.split()), False)
                        if not CHECK:
                            self.blocos[cod] = NaoMapeado_block()
                        bloco = self.blocos[cod]
                        
                    dados = super()._interpretarLinha(bloco.campos,row)
                    dados['_comentarioAnterior'] = deepcopy(comentarios)
                    bloco.valores.append(dados)
                    comentarios=[]
        if comentarios!=[]:
            self.rodape = deepcopy(comentarios)



    def save(self):
        dadgnl = super()._saveToFile(self.blocos.values()) + ("\n" + "\n".join(self.rodape)).encode("latin-1")
        return dadgnl
    