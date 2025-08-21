def getBlocosMnemonico(mnemonic):
    if mnemonic=='HQ':
        return HQLine().campos,"HQLine"
    elif mnemonic=='LQ':
        return LQLine().campos,"LQLine"
    elif mnemonic=='CQ':
        return CQLine().campos,"CQLine"
  


class HQLine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio Ini"),
                ( 15 , 16,"I2"    , "Estagio Fim"),
                ]
        self.valores = []

class LQLine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio"),
                ( 15 , 24,"F10.2*" , "INF1"),
                ( 25 , 34,"F10.2*" , "SUP1"),
                ( 35 , 44,"F10.2*" , "INF2"),
                ( 45 , 54,"F10.2*" , "SUP2"),
                ( 55 , 64,"F10.2*" , "INF3"),
                ( 65 , 74,"F10.2*" , "SUP3"),
                ]
        self.valores = []

class CQLine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio"),
                ( 15 , 17,"I3"    , "Usina"),
                ( 20 , 29,"F10.1" , "Coeficiente"),
                ( 35 , 38,"A4"    , "Tipo"),
                ]

        self.valores = []