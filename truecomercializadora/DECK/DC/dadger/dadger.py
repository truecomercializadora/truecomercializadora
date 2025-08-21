from truecomercializadora.DECK.utils import UTILS
from copy import deepcopy
lastDados = {}
from DECK.DC.dadger import ac, rhq, rhe, rhv, hecm

class HE_CM(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [( 1 , 2 ,"A2"  , "Id")]
        self.valores = []

class HV_LV_CV_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [( 1 , 2 ,"A2"  , "Id")]
        self.valores = []

class RE_LU_FU_FT_FI_FE_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [( 1 , 2 ,"A2"  , "Id")]
        self.valores = []

class HQ_CQ_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [( 1 , 2 ,"A2"  , "Id")]
        self.valores = []

class TI_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 7 ,"I3", "Usina"  ),
                ( 10, 14 ,"F5.1", "Fator1"  ), 
                ( 15, 19 ,"F5.1*", "Fator2"  ),
                ( 20, 24 ,"F5.1*", "Fator3"  ),
                ( 25, 29 ,"F5.1*", "Fator4"  ),
                ( 30, 34 ,"F5.1*", "Fator5"  ),
                ( 35, 39 ,"F5.1*", "Fator6"  ),
                ( 40, 44 ,"F5.1*", "Fator7"  ),
                ( 45, 49 ,"F5.1*", "Fator8"  ),
                ( 50, 54 ,"F5.1*", "Fator9"  ),
                ( 55, 59 ,"F5.1*", "Fator10"  ),
                ( 60, 64 ,"F5.1*", "Fator11"  ),
                ( 65, 69 ,"F5.1*", "Fator12"  ),
                ( 70, 74 ,"F5.1*", "Fator13"  ),
                ( 75, 79 ,"F5.1*", "Fator14"  ),
                ( 80, 84 ,"F5.1*", "Fator15"  ),
                ( 85, 89 ,"F5.1*", "Fator16"  ),
                ( 90, 94 ,"F5.1*", "Fator17"  ),
                ]
        self.valores = []

class FD_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 7 ,"I3", "Usina"  ),
                ( 8 , 9 ,"I2*", "Freq Itaipu"  ),
                ( 10, 14 ,"F5.3", "Fator1"  ), 
                ( 15, 19 ,"F5.3*", "Fator2"  ),
                ( 20, 24 ,"F5.3*", "Fator3"  ),
                ( 25, 29 ,"F5.3*", "Fator4"  ),
                ( 30, 34 ,"F5.3*", "Fator5"  ),
                ( 35, 39 ,"F5.3*", "Fator6"  ),
                ( 40, 44 ,"F5.3*", "Fator7"  ),
                ( 45, 49 ,"F5.3*", "Fator8"  ),
                ( 50, 54 ,"F5.3*", "Fator9"  ),
                ( 55, 59 ,"F5.3*", "Fator10"  ),
                ( 60, 64 ,"F5.3*", "Fator11"  ),
                ( 65, 69 ,"F5.3*", "Fator12"  ),
                ( 70, 74 ,"F5.3*", "Fator13"  ),
                ( 75, 79 ,"F5.3*", "Fator14"  ),
                ( 80, 84 ,"F5.3*", "Fator15"  ),
                ( 85, 89 ,"F5.3*", "Fator16"  ),
                ( 90, 94 ,"F5.3*", "Fator17"  ),
                ]
        self.valores = []



class MP_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 7 ,"I3", "Usina"  ),
                ( 8 , 9 ,"I2*", "FreqItaipu"  ),
                ( 10, 14 ,"F5.3", "Fator1"  ),
                ( 15, 19 ,"F5.3*", "Fator2"  ),
                ( 20, 24 ,"F5.3*", "Fator3"  ),
                ( 25, 29 ,"F5.3*", "Fator4"  ),
                ( 30, 34 ,"F5.3*", "Fator5"  ),
                ( 35, 39 ,"F5.3*", "Fator6"  ),
                ( 40, 44 ,"F5.3*", "Fator7"  ),
                ( 45, 49 ,"F5.3*", "Fator8"  ),
                ( 50, 54 ,"F5.3*", "Fator9"  ),
                ( 55, 59 ,"F5.3*", "Fator10"  ),
                ( 60, 64 ,"F5.3*", "Fator11"  ),
                ( 65, 69 ,"F5.3*", "Fator12"  ),
                ( 70, 74 ,"F5.3*", "Fator13"  ),
                ( 75, 79 ,"F5.3*", "Fator14"  ),
                ( 80, 84 ,"F5.3*", "Fator15"  ),
                ( 85, 89 ,"F5.3*", "Fator16"  ),
                ( 90, 94 ,"F5.3*", "Fator17"  ),
                ]
        self.valores = []




class UH_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 11,"I2*"    , "Subsistema"),
                ( 15 , 24,"F10.2*" , "Volume Ini"),
                ( 25 , 34,"F10.0*" , "Vazao Deflu Min"),
                ( 35 , 36,"I2*"    , "Num valores FPEA"),
                ( 40 , 40,"I1*"    , "Evaporacao"),               
                ( 45 , 46,"I2*"    , "Estagio"),               
                ( 50 , 59,"F10.0*"    , "Volume Morto Ini"),               
                ( 60 , 69,"F10.0*"    , "Limite Vertimento"),               
                ( 70 , 73,"A1"    , "Bal Hidr Patamar"),     
                ]
        self.valores = []


class CT_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"   ,"Id" ),
                ( 5 , 7 ,"I3"   ,"Usina" ),
                ( 10 ,11,"I2"   ,"Subsistema" ),
                ( 15 ,24,"A10"  ,"Nome" ),
                ( 25 ,26,"I2"   ,"Estagio" ),
                ( 30 ,34,"F5.1" ,"Ger Min Pat1" ),
                ( 35 ,39,"F5.1" ,"Capacidade Pat1" ),
                ( 40 ,49,"F10.2","CVU Pat1" ),
                ( 50 ,54,"F5.1" ,"Ger Min Pat2" ),
                ( 55 ,59,"F5.1" ,"Capacidade Pat2" ),
                ( 60 ,69,"F10.2","CVU Pat2" ),
                ( 70 ,74,"F5.1" ,"Ger Min Pat3" ),
                ( 75 ,79,"F5.1" ,"Capacidade Pat3" ),
                ( 80 ,89,"F10.2","CVU Pat3" )
                ]
        self.valores = []

class AC_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"I3"    , "Usina"),
                ( 10 , 15,"A6"    , "Mnemonico"),
                ]
        self.valores = []

class DP_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"   ,"Id" ),
                ( 5 , 6 ,"I2"   ,"Estagio" ),
                ( 10 ,11,"I2"   ,"Subsistema" ),
                ( 15 ,15,"I1"  ,"Patamares" ),
                ( 20 ,29,"F10.1*" ,"Carga Pat1" ),
                ( 30 ,39,"F10.1" ,"Duracao Pat1" ),
                ( 40 ,49,"F10.1*" ,"Carga Pat2" ),
                ( 50 ,59,"F10.1" ,"Duracao Pat2" ),
                ( 60 ,69,"F10.1*" ,"Carga Pat3" ),
                ( 70 ,79,"F10.1" ,"Duracao Pat3" ),
                ]
        self.valores = []

class CD_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"   ,"Id" ),
                ( 5 , 6 ,"I2"   ,"Numero" ),
                ( 10 ,11,"I2"   ,"Subsistema" ),
                ( 15 ,24,"A10"   ,"Nome" ),
                ( 25 ,26 ,"I2"   ,"Estagio" ),                
                ( 30,	34,"F5.0" ,"Intervalo Pat1" ),
                ( 35,	44,"F10.2" ,"Custo Pat1" ),                
                ( 45,	49,"F5.0" ,"Intervalo Pat2" ),
                ( 50,	59,"F10.2" ,"Custo Pat2" ),                
                ( 60,	64,"F5.0" ,"Intervalo Pat3" ),
                ( 65,	74,"F10.2" ,"Custo Pat3" ),
                ]
        self.valores = []

class EA_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 6 ,"I2"  , "Sistema"),
                ( 10 , 19 ,"F10.0", "ENA m-1"  ),
                ( 20 , 29 ,"F10.0", "ENA m-2"  ),
                ( 30,  39 ,"F10.0", "ENA m-3"  ),
                ( 40,  49 ,"F10.0", "ENA m-4"  ),
                ( 50,  59 ,"F10.0", "ENA m-5"  ),
                ( 60,  69 ,"F10.0", "ENA m-6"  ),
                ( 70,  79 ,"F10.0", "ENA m-7"  ),
                ( 80,  89 ,"F10.0", "ENA m-8"  ),
                ( 90,  99 ,"F10.0", "ENA m-9"  ),
                ( 100, 109 ,"F10.0", "ENA m-10"  ),
                ( 110, 119 ,"F10.0", "ENA m-11"  ),
                ]
        self.valores = []

class ES_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 6 ,"I2"  , "Sistema"),
                ( 10 , 10 ,"I1", "Semanas"  ),
                ( 15 , 24 ,"F10.0", "ENA s-1"  ),
                ( 25 , 34 ,"F10.0", "ENA s-2"  ),
                ( 35 , 44 ,"F10.0", "ENA s-3"  ),
                ( 45 , 54 ,"F10.0", "ENA s-4"  ),
                ( 55 , 64 ,"F10.0", "ENA s-5"  ),
                ]
        self.valores = []

class EZ_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 7 ,"I3", "Usina"  ),
                ( 10 , 14 ,"F5.1", "Percentual"  ),
                ]
        self.valores = []

class FC_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 10 ,"A6", "Mnemonico"  ),
                ( 15 , 74 ,"A60", "Arquivo"  ),
                ]
        self.valores = []

class IA_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"   ,"Id" ),
                ( 5 , 6 ,"I2"   ,"Estagio" ),                
                ( 10, 11 ,"A2"   ,"Subsistema 1" ),
                ( 15, 16,"A2"   ,"Subsistema 2"  ),                                
                ( 18 ,18 ,"I1*"   ,"Penalidade" ), 
                ( 20, 29,"F10.0" ,"1-2 Pat1" ),
                ( 30, 39,"F10.0" ,"2-1 Pat1" ),                
                ( 40, 49,"F10.0" ,"1-2 Pat2" ),
                ( 50, 59,"F10.0" ,"2-1 Pat2" ),                
                ( 60, 69,"F10.0" ,"1-2 Pat3" ),
                ( 70, 79,"F10.0" ,"2-1 Pat3" ),  
                ]
        self.valores = []

class IT_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"   ,"Id" ),
                ( 5 , 6 ,"I2"   ,"Estagio" ),                
                ( 10, 12 ,"I3"   ,"Cod Itaipu" ),
                ( 15, 16,"I2"   ,"Subsistema" ),                                
                ( 20, 24,"F5.0" ,"Geracao Pat1" ),
                ( 25, 29,"F5.0" ,"Ande Pat1" ),                
                ( 30, 34,"F5.0" ,"Geracao Pat2" ),
                ( 35, 39,"F5.0" ,"Ande Pat2" ),                
                ( 40, 44,"F5.0" ,"Geracao Pat3" ),
                ( 45, 49,"F5.0" ,"Ande Pat3" ),
                ]
        self.valores = []

class ME_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 7 ,"I3", "Estacao"  ),
                ( 10, 11,"I2", "Subsistema"  ),
                ( 15, 19 ,"F5.0", "Fator1"  ),
                ( 20, 24 ,"F5.0", "Fator2"  ),
                ( 25, 29 ,"F5.0", "Fator3"  ),
                ( 30, 34 ,"F5.0", "Fator4"  ),
                ( 35, 39 ,"F5.0", "Fator5"  ),
                ( 40, 44 ,"F5.0", "Fator6"  ),
                ( 45, 49 ,"F5.0", "Fator7"  ),
                ( 50, 54 ,"F5.0", "Fator8"  ),
                ( 55, 59 ,"F5.0", "Fator9"  ),
                ( 60, 64 ,"F5.0", "Fator10"  ),
                ( 65, 69 ,"F5.0", "Fator11"  ),
                ( 70, 74 ,"F5.0", "Fator12"  ),
                ( 75, 79 ,"F5.0", "Fator13"  ),
                ( 80, 84 ,"F5.0", "Fator14"  ),
                ( 85, 89 ,"F5.0", "Fator15"  ),
                ( 90, 94 ,"F5.0", "Fator16"  ),
                ( 95, 99 ,"F5.0", "Fator17"  ),   
                ]
        self.valores = []

class MT_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 7 ,"I3", "Usina"  ),
                ( 10, 11 ,"I2", "Sistema"  ), 
                ( 15, 19 ,"F5.3", "Fator1"  ),
                ( 20, 24 ,"F5.3*", "Fator2"  ),
                ( 25, 29 ,"F5.3*", "Fator3"  ),
                ( 30, 34 ,"F5.3*", "Fator4"  ),
                ( 35, 39 ,"F5.3*", "Fator5"  ),
                ( 40, 44 ,"F5.3*", "Fator6"  ),
                ( 45, 49 ,"F5.3*", "Fator7"  ),
                ( 50, 54 ,"F5.3*", "Fator8"  ),
                ( 55, 59 ,"F5.3*", "Fator9"  ),
                ( 60, 64 ,"F5.3*", "Fator10"  ),
                ( 65, 69 ,"F5.3*", "Fator11"  ),
                ( 70, 74 ,"F5.3*", "Fator12"  ),
                ( 75, 79 ,"F5.3*", "Fator13"  ),
                ( 80, 84 ,"F5.3*", "Fator14"  ),
                ( 85, 89 ,"F5.3*", "Fator15"  ),
                ( 90, 94 ,"F5.3*", "Fator16"  ),
                ( 95, 99 ,"F5.3*", "Fator17"  ),
                ]
        self.valores = []

class PQ_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 14 ,"A10"  , "Usina"),
                ( 15 , 16 ,"I2", "Mercado"  ),
                ( 20 , 21 ,"I2", "Estagio"  ),
                ( 25 , 29 ,"F5.0", "Pat 1"  ),
                ( 30 , 34 ,"F5.0", "Pat 2"  ),
                ( 35 , 39 ,"F5.0", "Pat 3"  ),
                ( 60 , 64 ,"F5.0*", "Fator de Perda"  ),
                ]
        self.valores = []

class QI_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 7 ,"I3", "Usina"  ),
                ( 10 , 14 ,"F5.0", "Qi s-1"  ),
                ( 15 , 19 ,"F5.0", "Qi s-2"  ),
                ( 20 , 24 ,"F5.0", "Qi s-3"  ),
                ( 25 , 29 ,"F5.0", "Qi s-4"  ),
                ( 30 , 34 ,"F5.0", "Qi s-5"  ),
                ]
        self.valores = []

class RI_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"   ,"Id" ),
                ( 5 , 7 ,"I3"   ,"Indice Itaipu" ),
                ( 9, 11 ,"I3"   ,"Estagio" ),
                ( 13, 15,"I3"   ,"Subsistema" ),
                ( 17, 23,"F7.1" ,"MIN60 Pat1" ),
                ( 24, 30,"F7.1" ,"MAX60 Pat1" ),
                ( 31, 37,"F7.1" ,"MIN50 Pat1" ),
                ( 38, 44,"F7.1" ,"MAX50 Pat1" ),
                ( 45, 51,"F7.1" ,"ANDE Pat1" ),
                ( 52, 58,"F7.1" ,"MIN60 Pat2" ),
                ( 59, 65,"F7.1" ,"MAX60 Pat2" ),
                ( 66, 72,"F7.1" ,"MIN50 Pat2" ),
                ( 73, 79,"F7.1" ,"MAX50 Pat2" ),
                ( 80, 86,"F7.1" ,"ANDE Pat2" ),
                ( 87, 93,"F7.1" ,"MIN60 Pat3" ),
                ( 94, 100,"F7.1" ,"MAX60 Pat3" ),
                ( 101, 107,"F7.1" ,"MIN50 Pat3" ),
                ( 108, 114,"F7.1" ,"MAX50 Pat3" ),
                ( 115, 121,"F7.1" ,"ANDE Pat3" ),
                ]
        self.valores = []

class RQ_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 6 ,"I2", "Ree"  ),
                ( 10, 14 ,"F5.0", "Fator1"  ), 
                ( 15, 19 ,"F5.0*", "Fator2"  ),
                ( 20, 24 ,"F5.0*", "Fator3"  ),
                ( 25, 29 ,"F5.0*", "Fator4"  ),
                ( 30, 34 ,"F5.0*", "Fator5"  ),
                ( 35, 39 ,"F5.0*", "Fator6"  ),
                ( 40, 44 ,"F5.0*", "Fator7"  ),
                ( 45, 49 ,"F5.0*", "Fator8"  ),
                ( 50, 54 ,"F5.0*", "Fator9"  ),
                ( 55, 59 ,"F5.0*", "Fator10"  ),
                ( 60, 64 ,"F5.0*", "Fator11"  ),
                ( 65, 69 ,"F5.0*", "Fator12"  ),
                ( 70, 74 ,"F5.0*", "Fator13"  ),
                ( 75, 79 ,"F5.0*", "Fator14"  ),
                ( 80, 84 ,"F5.0*", "Fator15"  ),
                ( 85, 89 ,"F5.0*", "Fator16"  ),
                ( 90, 94 ,"F5.0*", "Fator17"  ),
                ]
        self.valores = []

class SB_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 6 ,"I2", "Subsistema"  ),
                ( 10 , 11 ,"A2", "Mnemonico"  ),
                ]
        self.valores = []

class TE_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 84 ,"A80", "Titulo"  ),
                ]
        self.valores = []

class UE_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1  , 2 ,"A2"    , "Id"),
                ( 5  , 7 ,"Z3"    , "Estacao"),
                ( 10 , 11,"I2"    , "Subsistema"),
                ( 15 , 26,"A12" , "Nome"),
                ( 30 , 32 ,"I3"    , "Montante"),
                ( 35 , 37 ,"I3"    , "Jusante"),
                ( 40 , 49,"F10.1" , "Vazao Min"),
                ( 50 , 59,"F10.1" , "Vazao Max"),
                ( 60 , 69,"F10.2" , "Consumo"),
                ]
        self.valores = []

class VE_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 7 ,"I3", "Usina"  ),
                ( 10, 14 ,"F5.3", "Sem1"  ), 
                ( 15, 19 ,"F5.3*", "Sem2"  ),
                ( 20, 24 ,"F5.3*", "Sem3"  ),
                ( 25, 29 ,"F5.3*", "Sem4"  ),
                ( 30, 34 ,"F5.3*", "Sem5"  ),
                ( 35, 39 ,"F5.3*", "Sem6"  ),
                ( 40, 44 ,"F5.3*", "Sem7"  ),
                ( 45, 49 ,"F5.3*", "Sem8"  ),
                ( 50, 54 ,"F5.3*", "Sem9"  ),
                ( 55, 59 ,"F5.3*", "Sem10"  ),
                ( 60, 64 ,"F5.3*", "Sem11"  ),
                ( 65, 69 ,"F5.3*", "Sem12"  ),
                ( 70, 74 ,"F5.3*", "Sem13"  ),
                ( 75, 79 ,"F5.3*", "Sem14"  ),
                ( 80, 84 ,"F5.3*", "Sem15"  ),
                ( 85, 89 ,"F5.3*", "Sem16"  ),
                ( 90, 94 ,"F5.3*", "Sem17"  ),
                ]
        self.valores = []

class VI_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 7 ,"I3", "Usina"  ),
                ( 10 , 12 ,"I3", "Tempo"  ),
                ( 15 , 19 ,"F5.0", "Qdef s-1"  ),
                ( 20 , 24 ,"F5.0", "Qdef s-2"  ),
                ( 25 , 29 ,"F5.0", "Qdef s-3"  ),
                ( 30 , 34 ,"F5.0", "Qdef s-4"  ),
                ( 35 , 39 ,"F5.0", "Qdef s-5"  ),
                ]
        self.valores = []

class CX_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
                ( 1 , 2 ,"A2"  , "Id"),
                ( 5 , 9 ,"I4"  , "UsiNW"),
                ( 10 , 14 ,"I4", "UsinaDC"  ),
                ]
        self.valores = []


class NaoMapeado_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = []
        self.valores = []

class DADGER(UTILS):
    def __init__(self,caminho):
        super().__init__()  # Chama o __init__ da classe base
        self.blocos = {}
        self.caminho = caminho
        self.blocosMapeados = {'AC':AC_block(),"CT":CT_block(), "UH":UH_block(), "MP":MP_block(), "FD":FD_block(), "TI":TI_block(),'HQ LQ CQ':HQ_CQ_block() ,'RE LU FU FI FT':RE_LU_FU_FT_FI_FE_block(),'HV LV CV':HV_LV_CV_block(),'HE CM':HE_CM(),'VL VU':NaoMapeado_block(),'DP':DP_block(),'CD':CD_block(),'EA':EA_block(), 'ES':ES_block(), 'EZ':EZ_block(), "FC":FC_block(), "IA":IA_block(), "IT":IT_block(),'ME':ME_block(),'MT':MT_block(), "PQ":PQ_block(), "QI":QI_block(),'RI':RI_block(), "RQ":RQ_block(), "SB":SB_block(), "TE":TE_block(), "UE":UE_block(), "VE":VE_block(), "VI":VI_block(), 'CX':CX_block()}
        self.rodape = []
        self.nome = "DADGER"
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
                        
                    if cod=="AC":
                        blocos, tipo = ac.getBlocosMnemonico(row[9:15].strip())
                        if blocos!=None:
                            dados = super()._interpretarLinha(blocos,row)
                            dados['_customBlock'] = f"ac.{dados['Mnemonico']}"

                    elif cod=="HQ" or cod=="LQ" or cod=="CQ":
                        blocos, tipo = rhq.getBlocosMnemonico(cod)
                        if blocos!=None:
                            dados = super()._interpretarLinha(blocos,row)
                            dados['_customBlock'] = f"rhq.{cod}"

                    elif cod=="RE" or cod=="LU" or cod=="FU" or cod=="FT" or cod=="FI" or cod=="FE":
                        blocos, tipo = rhe.getBlocosMnemonico(cod)
                        if blocos!=None:
                            dados = super()._interpretarLinha(blocos,row)
                            dados['_customBlock'] = f"rhe.{cod}"
                    
                    elif cod=="HV" or cod=="LV" or cod=="CV":
                        blocos, tipo = rhv.getBlocosMnemonico(cod)
                        if blocos!=None:
                            dados = super()._interpretarLinha(blocos,row)
                            dados['_customBlock'] = f"rhv.{cod}"

                    elif cod=="HE" or cod=="CM":
                        blocos, tipo = hecm.getBlocosMnemonico(cod)
                        if blocos!=None:
                            dados = super()._interpretarLinha(blocos,row)
                            dados['_customBlock'] = f"hecm.{cod}"
                    else:
                        dados = super()._interpretarLinha(bloco.campos,row)

                    dados['_comentarioAnterior'] = deepcopy(comentarios)
                    bloco.valores.append(dados)
                    comentarios=[]
        if comentarios!=[]:
            self.rodape = deepcopy(comentarios)



    def save(self):
        dadger = super()._saveToFile(self.blocos.values()) + ("\n" + "\n".join(self.rodape) +"\n").encode("latin-1")
        return dadger
    