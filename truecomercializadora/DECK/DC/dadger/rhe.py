def getBlocosMnemonico(mnemonic):
    if mnemonic=='RE':
        return RELine().campos,"RELine"
    elif mnemonic=='LU':
        return LULine().campos,"LULine"
    elif mnemonic=='FU':
        return FULine().campos,"FULine"
    elif mnemonic=='FT':
        return FTLine().campos,"FTLine"
    elif mnemonic=='FI':
        return FILine().campos,"FILine"
    elif mnemonic=='FE':
        return FELine().campos,"FELine"

  


class RELine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 8 ,"I4"   , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio Ini"),
                ( 15 , 16,"I2"    , "Estagio Fim"),
                ]
        self.valores = []

class LULine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 8 ,"I4"    , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio"),
                ( 15 , 24,"F10.2*" , "GMIN1"),
                ( 25 , 34,"F10.2*" , "GMAX1"),
                ( 35 , 44,"F10.2*" , "GMIN2"),
                ( 45 , 54,"F10.2*" , "GMAX2"),
                ( 55 , 64,"F10.2*" , "GMIN3"),
                ( 65 , 74,"F10.2*" , "GMAX3"),
                ]
        self.valores = []

class FULine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 8 ,"I4"   , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio"),
                ( 15 , 17,"I3"    , "Usina"),
                ( 20 , 29,"F10.1" , "Fator"),
                ( 31 , 32,"I2*" , "Freq Itaipu"),
                ]

        self.valores = []

class FTLine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 8 ,"I4"  , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio"),
                ( 15 , 17,"I3"    , "Usina"),
                ( 20 , 21,"I2"    , "Subsistema"),
                ( 25 , 34,"F10.1" , "Fator"),
                ]

        self.valores = []
class FILine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 8 ,"I4"   , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio"),
                ( 15 , 16,"A2"    , "De"),
                ( 20 , 21,"A2"    , "Para"),
                ( 25 , 34,"F10.1" , "Fator"),
                ]

        self.valores = []
class FELine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 8 ,"I4"    , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio"),
                ( 15 , 17,"I3"    , "Contrato"),
                ( 20 , 21,"I1"    , "Submercado"),
                ( 25 , 34,"F10.1" , "Fator"),
                ]

        self.valores = []