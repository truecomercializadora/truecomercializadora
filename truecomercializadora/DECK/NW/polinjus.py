from truecomercializadora.DECK.utils import UTILS
from copy import deepcopy
lastDados = {}

class _bloco1(UTILS):
    def __init__(self):
        self.linhaIdentificador = "HIDRELETRICA-CURVAJUSANTE"
        self.campos = [
                ( 1 , None ,"A45"  , "COMENTARIO"),
                ( 2 , None ,"Z4", "Usina"  ),
                ( 3, None ,"Z3", "Indice"  ), 
                ( 4, None ,"F10.4", "HjusRef"  ),
                ]
        self.valores = None


class _bloco2(UTILS):
    def __init__(self):
        self.linhaIdentificador = "HIDRELETRICA-CURVAJUSANTE-POLINOMIOPORPARTES"
        self.campos = [
                ( 1 , None ,"A45"  , "COMENTARIO"),
                ( 2 , None ,"Z4", "Usina"  ),
                ( 3, None ,"Z3", "Indice"  ), 
                ( 4, None ,"Z3", "nPol"  ),
                ]
        self.valores = None

class _bloco3(UTILS):
    def __init__(self):
        self.linhaIdentificador = "HIDRELETRICA-CURVAJUSANTE-POLINOMIOPORPARTES-SEGMENTO"
        self.campos = [
                ( 1 , None ,"A53"  , "COMENTARIO"),
                ( 2 , None ,"Z4", "Usina"  ),
                ( 3, None ,"Z3", "IndCurva"  ), 
                ( 4, None ,"I2", "IndPolin"  ), 
                ( 5, None ,"F20.3", "QjusMin"  ),
                ( 6, None ,"F20.3", "QjusMax"  ),
                ( 7, None ,"A20", "a0"  ),
                ( 8, None ,"A20", "a1"  ),
                ( 9, None ,"A20", "a2"  ),
                ( 10, None ,"A20", "a3"  ),
                ( 11, None ,"A20", "a4"  ),
                ]
        self.valores = None


class _bloco4(UTILS):
    def __init__(self):
        self.linhaIdentificador = "HIDRELETRICA-CURVAJUSANTE-AFOGAMENTO-EXPLICITO-USINA"
        self.campos = [
                ( 1 , None ,"A52"  , "COMENTARIO"),
                ( 2 , None ,"Z4", "Usina"  ),
                ( 3, None ,"A3", "FLAG"  ), 
                ]
        self.valores = None


class polinjus(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = []
        self.valores = []
        self.csv = True


class POLINJUS(UTILS):
    def __init__(self,caminho):
        self.csv = True
        self.blocos = {'polinjus':polinjus(),'_bloco1':_bloco1(),'_bloco2':_bloco2(),'_bloco3':_bloco3(),'_bloco4':_bloco4()}
        self.caminho = caminho
        self.rodape = []
        self.polinjus = self.blocos['polinjus']
        self.nome = "POLINJUS"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()



    def load(self):
        dados = self.abrir_arquivo_com_codificacao_automatica()

        comentarios = []
        for row in dados:
                if row.startswith(" &") or len(row.strip())==0:
                    comentarios.append(row)
                else:
                    for bloco in reversed(self.blocos.values()):
                        try:
                            if bloco.linhaIdentificador in row:
                                dadosRow = super()._interpretarLinha(bloco.campos,row)
                                dadosRow['_comentarioAnterior'] = deepcopy(comentarios)
                                self.polinjus.valores.append(dadosRow)
                                break
                            else: continue
                        except:pass
                    comentarios=[]
        if comentarios!=[]:
            self.rodape = deepcopy(comentarios)



    def save(self):
        polinjusFinal = []
        for row in self.polinjus.valores:
            for bloco in reversed(self.blocos.values()):
                    try:
                        if bloco.linhaIdentificador in row['COMENTARIO']:
                            if "_comentarioAnterior" in row.keys():
                                for item in row['_comentarioAnterior']:
                                    polinjusFinal.append(item)
                            dadosLine = []
                            for inicio, fim, tipo, chave in bloco.campos:
                                valor = str(row[chave])
                                dadosLine.append(super()._saveLine(valor,tipo))
                            polinjusFinal.append(";".join(dadosLine))
                            break
                        else: continue
                    except:
                        pass
        polinjusFinal.append("\n")
        return "\n".join(polinjusFinal)
    