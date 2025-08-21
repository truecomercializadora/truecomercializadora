from truecomercializadora.DECK.utils import UTILS
from copy import deepcopy
lastDados = {}

class _bloco1(UTILS):
    def __init__(self):
        self.linhaIdentificador = "CADH-VOL-REF-PER"
        self.campos = [
                ( 1 , None ,"A16"  , "COMENTARIO"),
                ( 2 , None ,"i3", "cod_rest"  ),
                ( 3, None ,"A7", "PerIni"  ), 
                ( 4, None ,"A7", "PerFim"  ), 
                ( 5, None ,"F3.2", "Valor"  ),
                ]
        self.valores = None


class volumesreferencia(UTILS):
    def __init__(self):
        self.cabecalho = "VOLUME-REFERENCIAL-TIPO-PADRAO;1;;;"
        self.campos = []
        self.valores = []
        self.csv = True


class VOLUMESREFERENCIA(UTILS):
    def __init__(self,caminho):
        self.csv = True
        self.blocos = {'volumesreferencia':volumesreferencia(),'_bloco1':_bloco1()}
        self.caminho = caminho
        self.rodape = []
        self.volumesreferencia = self.blocos['volumesreferencia']
        self.nome = "VOLUME-REFERENCIA"
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
                                self.volumesreferencia.valores.append(dadosRow)
                                break
                            else: continue
                        except:pass
                    comentarios=[]
        if comentarios!=[]:
            self.rodape = deepcopy(comentarios)



    def save(self):
        volumesreferenciaFinal = []
        volumesreferenciaFinal.append(self.blocos['volumesreferencia'].cabecalho)
        for row in self.volumesreferencia.valores:
            for bloco in reversed(self.blocos.values()):
                    try:
                        if bloco.linhaIdentificador in row['COMENTARIO']:
                            if "_comentarioAnterior" in row.keys():
                                for item in row['_comentarioAnterior']:
                                    volumesreferenciaFinal.append(item)
                            dadosLine = []
                            for inicio, fim, tipo, chave in bloco.campos:
                                valor = str(row[chave])
                                dadosLine.append(super()._saveLine(valor,tipo))
                            volumesreferenciaFinal.append(";".join(dadosLine))
                            break
                        else: continue
                    except:
                        pass
        volumesreferenciaFinal.append("")
        return "\n".join(volumesreferenciaFinal)
    