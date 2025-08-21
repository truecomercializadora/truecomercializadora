def getBlocosMnemonico(mnemonic):
    if mnemonic in ["NOMEUH", "TIPUSI"]:
        return AcA12Line().campos,'AcA12Line'
    elif mnemonic in [
        "NUMPOS", "NUMJUS", "NUMCON", "VERTJU", "VAZMIN", 
        "NUMBAS", "TIPTUR", "TIPERH", "JUSENA"
    ]:
        return AcI5Line().campos,'AcI5Line'
    elif mnemonic in ["ALTEFE", "NCHAVE"]:
        return AcI5D102Line().campos,'AcI5D102Line'
    elif mnemonic in ["POTEFE"]:
        return AcI5D101Line().campos,'AcI5F101Line'
    elif mnemonic in ["DESVIO"]:
        return AcI5D100Line().campos,'AcI5D100Line'
    elif mnemonic in [
        "VOLMAX", "PERHID", "JUSMED"]:
        return AcF10Line().campos,'AcF10Line'
    elif mnemonic in ["VOLMIN"]:
        return AcF100Line().campos,'AcF100Line'

    elif mnemonic in [
        "VSVERT", "VMDESV"
    ]:
        return AcF102Line().campos,'AcF102Line'
    elif mnemonic == "PROESP":
        return AcF10Lineext().campos, 'AcF10Lineext'
    elif mnemonic in ["COFEVA", "NUMMAQ", "VAZEFE"]:
        return Ac2I5Line().campos, 'Ac2I5Line'
    elif mnemonic in ["COTVOL", "COTARE"]:
        return AcI5E15Line().campos, 'AcI5E15Line'
    elif mnemonic == "COTVAZ":
        return Ac2I5E15Line().campos, 'Ac2I5E15Line'
    elif mnemonic == "VAZCCF":
        return AcF10I5F10Line().campos, 'AcF10I5F10Line'
    else: return AcLine().campos,'AcLine'


class AcLine():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 59,"A40"   , "Parametros"),
                ( 60 , 60,"A1"    , ""),
                ( 61 , 61,"A1"    , ""),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcA1Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 20,"A1"    , "p1"),
                ( 60 , 60,"A1"    , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcA12Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 31,"A12"   , "p1"),
                ( 60 , 60,"A1"    , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcI5Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 24,"I5"    , "p1"),
                ( 60 , 60,"A1"    , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class Ac2I5Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 24,"I5"    , "p1"),
                ( 25 , 29,"I5"    , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcF10Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 29,"F10.2"    , "p1"),
                ( 60 , 60,"A1"    , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcF100Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 29,"F10.0"    , "p1"),
                ( 60 , 60,"A1"    , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcF102Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 29,"F10.0."    , "p1"),
                ( 60 , 60,"A1"    , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcF10Lineext():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 29,"F10.6"    , "p1"),
                ( 60 , 60,"A1"    , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcI5D101Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 24,"I5"    , "p1"),
                ( 25 , 34,"F10.1" , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcI5D102Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 24,"I5"    , "p1"),
                ( 25 , 34,"F10.2" , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcI5D100Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 24,"I5"    , "p1"),
                ( 25 , 34,"F10.0." , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcF10I5F10Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 29,"F10.0" , "p1"),
                ( 30 , 34,"I5"    , "p2"),
                ( 35 , 44,"F10.0" , "p3"),                
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

class AcI5E15Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 24,"I5"    , "p1"),
                ( 25 , 39,"E15.7" , "p2"),
                ( 61 , 61,"A1"    , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []


class Ac2I5E15Line():
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ( 20 , 24,"I5"    , "p1"),
                ( 25 , 29,"I5"    , "p2"),
                ( 30 , 44,"E15.7" , "p3"),
                ( 70 , 73,"A3"    , "Mes"),
                ( 75 , 75,"I1*"    , "Semana"),
                ( 77 , 80,"I4*"    , "Ano"),
                ]
        self.valores = []

    