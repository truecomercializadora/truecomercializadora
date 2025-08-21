def getBlocosMnemonico(mnemonic):
    if mnemonic=='HV':
        return HVLine().campos,"HVLine"
    elif mnemonic=='LV':
        return LVLine().campos,"LVLine"
    elif mnemonic=='CV':
        return CVLine().campos,"CVLine"
  


class HVLine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio Ini"),
                ( 15 , 16,"I2"    , "Estagio Fim"),
                ]
        self.valores = []

class LVLine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Restricao"),
                ( 10 , 11,"I2"    , "Estagio"),
                ( 15 , 24,"F10.2*" , "INF"),
                ( 25 , 34,"F10.2*" , "SUP"),
                ]
        self.valores = []

class CVLine():
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