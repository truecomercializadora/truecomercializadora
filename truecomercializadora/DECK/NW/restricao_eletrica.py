from truecomercializadora.DECK.utils import UTILS
from copy import deepcopy
lastDados = {}

class _bloco1(UTILS):
    def __init__(self):
        self.linhaIdentificador = "RE"
        self.campos = [
                ( 1 , None ,"A3"  , "COMENTARIO"),
                ( 2 , None ,"I9", "cod_rest"  ),
                ( 3, None ,"A20", "formula"  ), 
                ]
        self.valores = None


class _bloco2(UTILS):
    def __init__(self):
        self.linhaIdentificador = "RE-HORIZ-PER"
        self.campos = [
                ( 1 , None ,"A12"  , "COMENTARIO"),
                ( 2 , None ,"I9", "cod_rest"  ),
                ( 3, None ,"A7", "PerIni"  ), 
                ( 4, None ,"A7", "PerFin"  ),
                ]
        self.valores = None

class _bloco3(UTILS):
    def __init__(self):
        self.linhaIdentificador = "RE-LIM-FORM-PER-PAT"
        self.campos = [
                ( 1 , None ,"A20"  , "COMENTARIO"),
                ( 2 , None ,"I9", "cod_rest"  ),
                ( 3, None ,"A7", "PerIni"  ), 
                ( 4, None ,"A7", "PerFin"  ), 
                ( 5, None ,"I6", "Pat"  ),
                ( 6, None ,"A10", "LimInf"  ),
                ( 7, None ,"A9", "LimSup"  ),

                ]
        self.valores = None


class restricaoeletrica(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = []
        self.valores = []
        self.csv = True


class RESTRICAOELETRICA(UTILS):
    def __init__(self,caminho):
        self.csv = True
        self.blocos = {'restricaoeletrica':restricaoeletrica(),'_bloco1':_bloco1(),'_bloco2':_bloco2(),'_bloco3':_bloco3()}
        self.caminho = caminho
        self.rodape = []
        self.restricaoeletrica = self.blocos['restricaoeletrica']
        self.nome = "RESTRICAO-ELETRICA"
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
                    for bloco in reversed(self.blocos.values()):
                        try:
                            if bloco.linhaIdentificador in row:
                                dadosRow = super()._interpretarLinha(bloco.campos,row)
                                dadosRow['_comentarioAnterior'] = deepcopy(comentarios)
                                self.restricaoeletrica.valores.append(dadosRow)
                                break
                            else: continue
                        except:pass
                    comentarios=[]
        if comentarios!=[]:
            self.rodape = deepcopy(comentarios)



    def save(self):
        restricaoeletricaFinal = []
        for row in self.restricaoeletrica.valores:
            for bloco in reversed(self.blocos.values()):
                    try:
                        if bloco.linhaIdentificador in row['COMENTARIO']:
                            if "_comentarioAnterior" in row.keys():
                                for item in row['_comentarioAnterior']:
                                    restricaoeletricaFinal.append(item)
                            dadosLine = []
                            for inicio, fim, tipo, chave in bloco.campos:
                                valor = str(row[chave])
                                dadosLine.append(super()._saveLine(valor,tipo))
                            restricaoeletricaFinal.append(";".join(dadosLine))
                            break
                        else: continue
                    except:
                        pass
        restricaoeletricaFinal.append("")
        return "\n".join(restricaoeletricaFinal)
    