from truecomercializadora.DECK.utils import UTILS
lastDados = {}



class VUTIL_block(UTILS):
    def __init__(self):
        self.cabecalho = '''   VOLUME UTIL DOS RESERVATORIOS                                                                                                                                                                        
   X----X------------X-------X------X------X------X------X------X------X                                                                                                                                
     No.  Usina        %V.U.          % V.U.  Final                                                                                                                                                     
                       Inic.  Sem_01 Sem_02 Sem_03 Sem_04 Sem_05 Sem_06                                                                                                                                 
   X----X------------X-------X------X------X------X------X------X------X    '''
        self.campos = [
                ( 4 , 8 ,"I4"  , "Cod"),
                ( 10 , 21 ,"A12"  , "Usina"),
                (23  , 29 ,"F6.1*"  , "VolIni"),
                (31  , 36 ,"F5.1*"  , "VolFinSem1"),
                (38  , 43 ,"F5.1*"  , "VolFinSem2"),
                (45  , 50 ,"F5.1*"  , "VolFinSem3"),
                (52  , 57 ,"F5.1*"  , "VolFinSem4"),
                (59  , 64 ,"F5.1*"  , "VolFinSem5"),
                (66  , 71 ,"F5.1*"  , "VolFinSem6"),      
                    ]
        self.valores = []
        self.endBlock = ' 999'

class RELATORIO_block(UTILS):
    def __init__(self):
        self.cabecalho = '''   RELATORIO  DA  OPERACAO                                                                                                                                                                              
                                                                                                                                                                                                                                                                                                                                                                                                                
      # Aproveitamento(s) com evaporacao                                                                                                                                                                
      * Aproveitamento(s) com tempo de viagem da afluencia                                                                                                                                              
      @ Aproveitamento(s) com cota abaixo da crista do vert.                                                                                                                                            
      $ Aproveitamento(s) de cabeceira : def.minima = zero                                                                                                                                              
   X----X-----------------X-----------------X----------------------------------X---------------------------------------------------------------X                                                        
    No.       Usina       Volume (% V.U.)         Vazoes   (M3/S)                Energia (MWmed) - CGC Pdisp                                                                                            
                           Ini.  Fin.  Esp.   Qnat   (  %MLT)   Qafl     Qdef    GER_1   GER_2   GER_3    Media   VT(*)   VNT            FPCGC                                                          
   X----X-----------------X-----X-----X-----X----------------X--------X--------X-------X-------X-------X-------X-------X-------X---------------X   '''
        self.campos = [
                ( 4 , 8 ,"I4"  , "Cod"),
                ( 10 , 26 ,"A16"  , "Usina"),
                (28  , 32 ,"F4.1*"  , "VolIni"),
                (34  , 38 ,"F4.1*"  , "VolFin"),
                (40  , 44 ,"F4.1*"  , "VolEsp"),
                (46  , 52 ,"F6.1*"  , "Qnat"),
                (55  , 60 ,"A5"  , "Qnat (%MLT)"),
                (63  , 70 ,"F7.1*"  , "Qafl"),
                (72  , 79 ,"F7.1*"  , "Qdef"),
                (81  , 87 ,"F6.1*"  , "GER_1"),
                (89  , 95 ,"F6.1*"  , "GER_2"),
                (97  , 103 ,"F6.1**"  , "GER_3"),
                (105  , 111 ,"F6.1**"  , "Media"),
                (113  , 119 ,"F6.1**"  , "VT"),
                (121  , 127 ,"F6.1**"  , "VNT"),
                (129  , 143 ,"F14.1**"  , "FPCGC"),
                (None, None, None, "SEMANA"),
                (None, None, None, "ESTAGIO")
  
                    ]
        self.valores = []
        self.endBlock = ' 999'

class CONVERGENCIA_block(UTILS):
    def __init__(self):
        self.cabecalho = '''   RELATORIO DE CONVERGENCIA DO PROCESSO ITERATIVO

   X----X------------X------------X----------------X--------|----------------------------------------------------------------------X
                                                            |             Primeiro mes - iteracoes forward
                                                            |----------------------------------------------------------------------X
                                                            |       Tot Def         |
     It      Zinf         Zsup            GAP        TEMPO  |-----------------------|----------------------------------------------X
          (1.0E+03 $)  (1.0E+03 $)        (%)               |  Demanda    Niv Seg   |  Num.   Tot. Inviab  Tot. Inviab  Tot. Inviab
                                                            |  (MWmed)    (MWmes)   | Inviab    (MWmed)      (m3/s)       (Hm3)
   X----X------------X------------X----------------X--------|----------X------------X-------X------------X------------X------------X'''
        self.campos = [
                ( 4 , 8 ,"I4"  , "It"),
                ( 10 , 21 ,"F11.1**"  , "Zinf"),
                (23  , 34 ,"F11.1**"  , "Zsup"),
                (36  , 51 ,"F15.7**"  , "GAP"),
                (53  , 60 ,"A7"  , "TEMPO"),
                (62  , 71 ,"F9.0.*"  , "Demanda"),
                (73  , 84 ,"F11.0*"  , "Niv Seg"),
                (86  , 92 ,"I6*"  , "Num. Inviab"),
                (94  , 105 ,"F11.0."  , "Tot. Inviab (MWmed)"),
                (107  , 118 ,"F11.0."  , "Tot. Inviab (m3/s)"),
                (120  , 131 ,"F11.0."  , "Tot. Inviab (Hm3)"),
                    ]
        self.valores = []
        self.endBlock = ' 999'


class RELATO(UTILS):
    def __init__(self,caminho):
        self.blocos = {'VUTIL':VUTIL_block(), 'RELATORIO':RELATORIO_block(), 'CONVERGENCIA':CONVERGENCIA_block()}
        self.caminho = caminho
        self.nome = "RELATO"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()


    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()
        blocoAtual = ""
        blocoIniciado = False
        ignorarLinhas = 0
        RELATORIO = False
        SEMANA=''
        ESTAGIO=''
        for row in dados:
            if ignorarLinhas>0:
                ignorarLinhas = ignorarLinhas-1
                continue
            if "VOLUME UTIL DOS RESERVATORIOS" in row:
                blocoAtual = "VUTIL"
                blocoIniciado = False
                ignorarLinhas = 2
            if "RELATORIO DE CONVERGENCIA DO PROCESSO ITERATIVO" in row:
                blocoAtual = "CONVERGENCIA"
                blocoIniciado = False
                ignorarLinhas = 6
            if row.strip()=="RELATORIO  DA  OPERACAO":
                RELATORIO = True
            elif RELATORIO and len(row.split("/"))==3 and "SEM" in row:
                SEMANA = int(row.strip().split("/")[1].split(" - ")[0][-2:])
                ESTAGIO = int(row.strip().split("/")[1].split(" - ")[1][-2:])
            elif RELATORIO and "No.       Usina       Volume (% V.U.)         Vazoes   (M3/S)                Energia (MWmed) - CGC Pdisp" in row:
                blocoAtual = "RELATORIO"
                blocoIniciado = False

            elif row.strip().startswith("X-") and blocoAtual!='':
                if not blocoIniciado: blocoIniciado=True
                else:
                    blocoIniciado=False
                    blocoAtual = ""
                    SEMANA= ''
                    ESTAGIO = ''
                continue


            # print(blocoIniciado,blocoAtual,SEMANA,RELATORIO)
            if blocoIniciado:
                ROW = super()._interpretarLinha(self.blocos[blocoAtual].campos,row)
                if RELATORIO:
                    ROW['SEMANA'] = SEMANA
                    ROW['ESTAGIO'] = ESTAGIO
                self.blocos[blocoAtual].valores.append(ROW)

    def save(self):
        return super()._saveToFile(self.blocos.values())
    