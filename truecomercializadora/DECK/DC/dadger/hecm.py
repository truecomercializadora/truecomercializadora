def getBlocosMnemonico(mnemonic):
    if mnemonic=='HE':
        return HELine().campos,"HELine"
    elif mnemonic=='CM':
        return CMLine().campos,"CMLine"



class HELine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I2"   , "Restricao"),
                ( 10 , 10,"I1"    , "TipoLimite"),
                ( 15, 24,"F10.1" , "LimInf"),
                ( 26, 27,"I2"    , "Estagio"),
                ( 29, 38,"F10.1" , "Penalidade"),
                ( 40 , 40,"I1*"    , "TipoCalculo"),
                ( 42 , 42,"I1*"    , "TipoValores"),
                ( 44 , 44,"I1*"    , "TipoTratamento"),
                (46  ,105 ,"A60"    , "Arquivo"),
                ( 107 , 107,"I1*"    , "TipoTolerancia"),
                ]
        self.valores = []

class CMLine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I2"    , "Restricao"),
                ( 10 , 12,"I3"    , "Ree"),
                ( 15 , 24,"F10.0" , "Coeficiente"),
                ]
        self.valores = []