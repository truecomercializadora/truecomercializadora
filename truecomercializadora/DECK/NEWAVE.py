import os
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta
from zipfile import ZipFile,ZIP_DEFLATED
from io import BytesIO
from truecomercializadora.DECK.utils import UTILS
from truecomercializadora.DECK.NW import agrint,c_adic,clast,confhd,conft,curva,cvar,dger,dsvagua,expt,ghmin,hidr,manutt,modif,patamar,penalid,postos,ree,sistema,term,vazoes,vazpast,volref_saz,restricao_eletrica,volumes_referencia,adterm
from truecomercializadora.DECK.DC import volume_sse,volume_uhe
ARQUIVOS_MAPEADOS = {"agrint":agrint.AGRINT, "c_adic":c_adic.C_ADIC, "cadic":c_adic.C_ADIC, "clast":clast.CLAST, "confhd":confhd.CONFHD, "conft":conft.CONFT, "curva":curva.CURVA, "cvar":cvar.CVAR, "dger":dger.DGER, "dsvagua":dsvagua.DSVAGUA, "expt":expt.EXPT, "ghmin":ghmin.GHMIN, "hidr":hidr.HIDR, "manutt":manutt.MANUTT, "modif":modif.MODIF, "patamar":patamar.PATAMAR, "penalid":penalid.PENALID, "postos":postos.POSTOS, "ree":ree.REE, "sistema":sistema.SISTEMA, "term":term.TERM, "vazoes":vazoes.VAZOES, "vazpast":vazpast.VAZPAST, "volref_saz":volref_saz.VOLREF_SAZ, "restricao-eletrica":restricao_eletrica.RESTRICAOELETRICA, "volumes-referencia":volumes_referencia.VOLUMESREFERENCIA, 'volume_uhe':volume_uhe.VOLUME_UHE, "volume_sse":volume_sse.VOLUME_SSE, "adterm":adterm.ADTERM}

class NEWAVE(UTILS):
    '''Aceita caminho do deck, Bytes de um zip ou ZipFile. Para bytes ou ZipFile é preciso passar a data do deck, caso tenha mais de um deck no zip'''
    def __init__(self,caminho,data=''):
        super().__init__()
        self.ARQUIVOS = {}
        self.caminho = caminho
        self.nomesOriginais = {}
        self.dataDeck = data
        self.MaxDataDeck = ''
        self.load()
        self.ERROS = self._checkErros()

    def load(self):
        if type(self.caminho)==str:
            for file in os.listdir(self.caminho):
                nomeArq = file.rsplit("/",1)[-1].lower().rsplit(".",1)[0]
                self.nomesOriginais[nomeArq] = file
                if nomeArq in ARQUIVOS_MAPEADOS.keys():
                    file = os.path.join(self.caminho,file)
                    self.ARQUIVOS[nomeArq] = ARQUIVOS_MAPEADOS[nomeArq](file)

        elif type(self.caminho)==bytes: #PARA USAR BYTES DEVE-SE PASSAR A DATA DO DECK SE TIVER MAIS DE UM DECK NO ZIP
            with ZipFile(BytesIO(self.caminho)) as dados:
                for file in [x for x in dados.namelist() if x.replace("\\",'/').split("/")[-1]!='']:
                    nomeArq = file.replace("\\",'/').split('/',1)[-1].lower().rsplit(".",1)[0]
                    self.nomesOriginais[nomeArq] = file
                    if nomeArq in ARQUIVOS_MAPEADOS.keys():
                        self.ARQUIVOS[nomeArq] = ARQUIVOS_MAPEADOS[nomeArq](dados.read(file))

        elif type(self.caminho)==ZipFile: #PARA USAR ZIPFILE DEVE-SE PASSAR A DATA DO DECK SE TIVER MAIS DE UM DECK NO ZIP
            for file in [x for x in self.caminho.namelist() if x.replace("\\",'/').split("/")[-1]!='' and f"NW{self.dataDeck:%Y%m}" in x]:
                nomeArq = file.replace("\\",'/').split('/',1)[-1].lower().rsplit(".",1)[0]
                self.nomesOriginais[nomeArq] = file
                if nomeArq in ARQUIVOS_MAPEADOS.keys():
                    self.ARQUIVOS[nomeArq] = ARQUIVOS_MAPEADOS[nomeArq](self.caminho.read(file))

        MES = int(self.ARQUIVOS['dger'].blocos['dger'].query({'Descricao':('contem','MES INICIO DO ESTUDO')})[0]["V1"])
        ANO = int(self.ARQUIVOS['dger'].blocos['dger'].query({'Descricao':('contem','ANO INICIO DO ESTUDO')})[0]["V1"])
        self.dataDeck = datetime(ANO,MES,1)
        self.MaxDataDeck = self.dataDeck+relativedelta(years=4)+relativedelta(month=12)

    def save(self,pasta=""):
        if type(self.caminho)==str or pasta!="":

            for file in self.ARQUIVOS.keys():
                try:
                    if self.ARQUIVOS[file].ERROS:
                        print(f"IGNORANDO ARQUIVO '{file}' POIS TEM ERROS:")
                        print("     "+"\n     ".join(self.ERROS[file]['MSG']))
                        print("     "+"\n     ".join(self.ERROS[file]['DETALHES']))
                        continue
                    if self.caminho == pasta and self.ARQUIVOS[file].hash == self.ARQUIVOS[file].gerarHash(): continue
                    dados = self.ARQUIVOS[file].save()
                    if pasta=="":
                        caminho = self.nomesOriginais[file]
                    else:
                        caminho = os.path.join(pasta,self.nomesOriginais[file].split("/")[-1])
                        os.makedirs(pasta,exist_ok=True)
                    if type(dados)==bytes:
                        open(caminho,'wb').write(dados)
                    else:
                        open(caminho,'w').write(dados)
                except:
                    import traceback;print(traceback.format_exc())
                    print(f"ERRO AO SALVAR ARQUIVO: {file}")

            
        elif type(self.caminho)==bytes:
            buffer = BytesIO()
            with ZipFile(BytesIO(self.caminho), 'r') as zip_in:
                with ZipFile(buffer, 'w', ZIP_DEFLATED) as zip_out:
                    for file_name in zip_in.namelist():
                        try:
                            file = file_name.rsplit("/",1)[-1].lower().rsplit(".",1)[0]
                            if "-sem" not in file_name.lower() and file in self.ARQUIVOS.keys():
                                if self.ARQUIVOS[file].ERROS:
                                    print(f"IGNORANDO ARQUIVO '{file}' POIS TEM ERROS:")
                                    print("     "+"\n     ".join(self.ERROS[file]['MSG']))
                                    print("     "+"\n     ".join(self.ERROS[file]['DETALHES']))
                                    continue
                                zip_out.writestr(file_name, self.ARQUIVOS[file].save())
                            else:
                                zip_out.writestr(file_name, zip_in.read(file_name))
                        except:
                            print(f"ERRO AO SALVAR ARQUIVO: {file_name}")

            buffer.seek(0)
            return buffer.getvalue()
        
        elif type(self.caminho)==ZipFile:
            zip_out = ZipFile(buffer, 'w', ZIP_DEFLATED)
            for file_name in self.caminho.namelist():
                try:
                    file = file_name.rsplit("/",1)[-1].lower().rsplit(".",1)[0]
                    if "-sem" not in file_name.lower() and file in self.ARQUIVOS.keys():
                        if self.ARQUIVOS[file].ERROS:
                            print(f"IGNORANDO ARQUIVO '{file}' POIS TEM ERROS:")
                            print("     "+"\n     ".join(self.ERROS[file]['MSG']))
                            print("     "+"\n     ".join(self.ERROS[file]['DETALHES']))
                            continue
                        zip_out.writestr(file_name, self.ARQUIVOS[file].save())
                    else:
                        zip_out.writestr(file_name, self.caminho.read(file_name))
                except:
                    print(f"ERRO AO SALVAR ARQUIVO: {file_name}")

            return zip_out

    def getDadosTermicas(self,usina,data=None):
        if data==None: data=self.dataDeck
        term = self.ARQUIVOS['term']
        expt =  self.ARQUIVOS['expt']
        manutt =  self.ARQUIVOS['manutt']
        conft =  self.ARQUIVOS['conft']
        clast =  self.ARQUIVOS['clast']

        conftUsina = [x for x in conft.conft.valores if x['Num']==usina][0]
        termUsina = [x for x in term.term.valores if x['Cod']==usina][0]
        exptUsina = [x for x in expt.expt.valores if x['Cod']==usina and x['DATA_INICIO']<=data and (x['DATA_FIM']=="" or x['DATA_FIM']>=data)]
        manuttUsina = [x for x in manutt.manutt.valores if x['Cod']==usina and data.strftime("%m-%Y") in x['DIAS_MES'].keys()]


        def getManutenções(manutencoes,data,POTEF):
            if len(manutencoes)==0: return 0
            manuttMes = 0
            for manutt in manutencoes:
                diasManutt = (manutt['DIAS_MES'][data.strftime("%m-%Y")])
                diasMes = calendar.monthrange(data.year, data.month)[1]
                if POTEF>0:
                    manuttMes+=(manutt['Potencia']/POTEF)*(diasManutt/diasMes)
            return manuttMes*100

        if conftUsina['E.Exist']=="EX":
            POTEF = termUsina['Potencia']
            FCMAX = termUsina['FCMX']/100
            TEIFT = termUsina['TEIF']/100
            if data.year==self.dataDeck.year:
                GTMIN = termUsina[f'GTMIN{data.month}']
                IPTER = getManutenções(manuttUsina,data,POTEF)
            else:
                GTMIN = termUsina['GTMIN D+ ANOS']
                IPTER = termUsina['IP']/100
        else:
            POTEF = next((x for x in exptUsina if x['Tipo'] == "POTEF"), {"Valor": 0})['Valor']
            FCMAX = next((x for x in exptUsina if x['Tipo'] == "FCMAX"), {"Valor": termUsina.get('FCMX', 0)})['Valor']/100
            if data.year==self.dataDeck.year:
                IPTER = next((x for x in exptUsina if x['Tipo'] == "IPTER"), {"Valor": getManutenções(manuttUsina,data,POTEF)})['Valor']/100
            else:
                IPTER = next((x for x in exptUsina if x['Tipo'] == "IPTER"), {"Valor": termUsina.get('IP', 0)})['Valor']/100
            TEIFT = next((x for x in exptUsina if x['Tipo'] == "TEIFT"), {"Valor": termUsina.get('TEIF', 0)})['Valor']/100
            GTMIN = next((x for x in exptUsina if x['Tipo'] == "GTMIN"), {"Valor": 0})['Valor']

        GTMAX = POTEF * FCMAX * round((1-IPTER),4) * round((1-TEIFT),4)

        ClastConjuntural = clast.blocos['conjunturais'].query({"DATA_INICIO":("<=",data),"DATA_FIM":(">=",data), "Num":usina})
        if self.hasValue(ClastConjuntural):
            CVU = ClastConjuntural[0]['CVU']
        else:
            ANO_REF = (data.year - self.dataDeck.year)+1
            ClastEstrutural = clast.blocos['estruturais'].query({"Num":usina})
            CVU = ClastEstrutural[0][f'CVU{ANO_REF}']

        return {"USINA": usina,"GTMAX":round(GTMAX,2), "GTMIN":round(GTMIN,2), "POTEF":POTEF, "FCMAX":FCMAX, "TEIF":TEIFT, "IPTER":IPTER, "CVU":CVU, "DATA":data}
    
    def getDadosTermicasHorizonte(self,usina):
        gtmax = []
        data = self.dataDeck
        while data!=self.MaxDataDeck+relativedelta(months=1):
            gtmax.append(self.getDadosTermicas(usina,data))
            data += relativedelta(months=1)
        return gtmax