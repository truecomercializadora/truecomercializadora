def getBlocosMnemonico(mnemonic):
    if mnemonic=='VA':
        return VALine().campos,"VALine"
    elif mnemonic=='VU':
        return VULine().campos,"VULine"
    elif mnemonic=='VL':
        return VLLine().campos,"VLLine"


class VALine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 3 ,"A3"    , "Id"),
                ( 5  , 8 ,"I4"   , "Usina"),
                ( 11 , 14,"I4*"    , "PostoInc"),
                ( 17 , 31,"F15.2*"    , "Fator"),
                ]
        self.valores = []

class VULine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 3 ,"A3"    , "Id"),
                ( 5  , 8 ,"I4"    , "Usina"),
                ( 11 , 14,"I4*"    , "UsinaDefl"),
                ( 17 , 31,"F15.2*" , "Fator"),
                ]
        self.valores = []

class VLLine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 3 ,"A3"    , "Id"),
                ( 5  , 8 ,"I4"   , "Usina"),
                ( 11 , 25,"F15.2*"    , "Fator"),
                ( 27 , 41,"F15.0*"    , "Coef0"),
                ( 43 , 57,"F15.0*" , "Coef1"),
                ( 59 , 73,"F15.0*" , "Coef2"),
                ( 75 , 89,"F15.0*" , "Coef3"),
                ( 91 , 105,"F15.0*" , "Coef4"),
                ]

        self.valores = []