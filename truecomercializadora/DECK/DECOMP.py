import os
from truecomercializadora.DECK.DC import prevs,regras, mlt, relato, volume_uhe, volume_sse, dadgnl, relgnl, inviab_unic
from truecomercializadora.DECK.DC.dadger import dadger
from truecomercializadora.DECK.NW import hidr, vazoes,postos,polinjus
from datetime import datetime,timedelta
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
from truecomercializadora.DECK.utils import UTILS
from dateutil.relativedelta import relativedelta

ARQUIVOS_MAPEADOS = {'dadger':dadger.DADGER,'vazoes':vazoes.VAZOES, 'postos':postos.POSTOS, 'polinjus':polinjus.POLINJUS, 'prevs':prevs.PREVS,'regras':regras.REGRAS, 'hidr':hidr.HIDR, 'mlt':mlt.MLT, 'relato':relato.RELATO, 'volume_uhe':volume_uhe.VOLUME_UHE, "volume_sse":volume_sse.VOLUME_SSE, 'dadgnl':dadgnl.DADGNL, 'outgnl':dadgnl.DADGNL, 'relgnl':relgnl.RELGNL, "inviab_unic":inviab_unic.INVIAB_UNIC}
ARQUIVOS_SAIDA = ['inviab_unic','relgnl','outgnl','relato'] #ARQUIVOS QUE NÂO SERAO REESCRITOS AO SALVAR DECK
class DECOMP(UTILS):
    '''Aceita caminho do deck, Bytes de um zip ou ZipFile. Para bytes ou ZipFile é preciso passar a data do deck, caso tenha mais de um deck no zip'''
    def __init__(self,caminho):
        super().__init__()
        self.ARQUIVOS = {}
        self.ARQUIVOS_NAO_MAPEADOS = {}
        self.caminho = caminho
        self.nomesOriginais = {}
        self.dataDeck = None
        self.rev = 0
        self.load()
        self.ERROS = self._checkErros()

    def load(self):
        if type(self.caminho)==str:
            for file in os.listdir(self.caminho):
                nomeArq = file.rsplit("/",1)[-1].lower().rsplit(".",1)[0]
                if 'polinjus.dat' in file.lower(): continue
                if "vazoes" in file.rsplit("/",1)[-1].lower() and ".dat" not in file.lower(): nomeArq = 'vazoesRV'
                self.nomesOriginais[nomeArq] = file
                if nomeArq in ARQUIVOS_MAPEADOS.keys():
                    file = os.path.join(self.caminho,file)
                    if 'dadger' in nomeArq: self.rev = file[-1]
                    self.ARQUIVOS[nomeArq] = ARQUIVOS_MAPEADOS[nomeArq](file)
                elif "." in file:
                    file = os.path.join(self.caminho,file)
                    self.ARQUIVOS_NAO_MAPEADOS[file.rsplit("/",1)[-1].lower()] = {'bytes':open(file,'rb').read(),'caminho':file}

        elif type(self.caminho)==bytes: #PARA USAR BYTES DEVE-SE PASSAR A DATA DO DECK SE TIVER MAIS DE UM DECK NO ZIP
            with ZipFile(BytesIO(self.caminho)) as dados:
                 for file in [x for x in dados.namelist() if x.replace("\\",'/').split("/")[-1]!='']:
                    nomeArq = file.replace("\\",'/').rsplit("/",1)[-1].lower().rsplit(".",1)[0]
                    if 'polinjus.dat' in file.lower(): continue
                    if "vazoes" in file.rsplit("/",1)[-1].lower() and ".dat" not in file.lower(): nomeArq = 'vazoesRV'
                    self.nomesOriginais[nomeArq] = file
                    if nomeArq in ARQUIVOS_MAPEADOS.keys():
                        if 'dadger' in nomeArq: self.rev = file[-1]
                        self.ARQUIVOS[nomeArq] = ARQUIVOS_MAPEADOS[nomeArq](dados.read(file))
                    elif "." in file:
                        self.ARQUIVOS_NAO_MAPEADOS[file.replace("\\",'/').rsplit("/",1)[-1].lower()] = {'bytes':dados.read(file),'caminho':file}
        elif type(self.caminho)==ZipFile: #PARA USAR ZIPFILE DEVE-SE PASSAR A DATA DO DECK SE TIVER MAIS DE UM DECK NO ZIP
            for file in [x for x in self.caminho.namelist() if x.replace("\\",'/').split("/")[-1]!='']:
                nomeArq = file.replace("\\",'/').rsplit("/",1)[-1].lower().rsplit(".",1)[0]
                if 'polinjus.dat' in file.lower():continue
                if "vazoes" in file.rsplit("/",1)[-1].lower() and ".dat" not in file.lower(): nomeArq = 'vazoesRV'
                self.nomesOriginais[nomeArq] = file
                if nomeArq in ARQUIVOS_MAPEADOS.keys():
                    if 'dadger' in nomeArq: self.rev = file[-1]
                    self.ARQUIVOS[nomeArq] = ARQUIVOS_MAPEADOS[nomeArq](self.caminho.read(file))
                elif "." in file:
                    self.ARQUIVOS_NAO_MAPEADOS[file.replace("\\",'/').rsplit("/",1)[-1].lower()] = {'bytes':self.caminho.read(file),'caminho':file}

        dtSTR = self.ARQUIVOS['dadger'].blocos['DT'].valores[0]['stringDados'].split()
        self.data = datetime(int(dtSTR[-1]),int(dtSTR[-2]),int(dtSTR[-3]))
        self.dataDeck = (datetime(int(dtSTR[-1]),int(dtSTR[-2]),int(dtSTR[-3])) + timedelta(days=6)) + relativedelta(day = 1)

    def save(self,pasta="",forceBytes = False, SaveNaoMapeados = []):
        if forceBytes:
            buffer = BytesIO()
            with ZipFile(buffer, 'w', ZIP_DEFLATED) as zip_out:
                for file in self.ARQUIVOS.keys():
                    try:
                        if file in ARQUIVOS_SAIDA: 
                            zip_out.writestr(self.nomesOriginais[file], self.ARQUIVOS[file].originalBytes)
                        else:
                            if self.ARQUIVOS[file].ERROS:
                                print(f"IGNORANDO ARQUIVO '{file}' POIS TEM ERROS:")
                                print("     "+"\n     ".join(self.ERROS[file]['MSG']))
                                print("     "+"\n     ".join(self.ERROS[file]['DETALHES']))
                                continue
                            zip_out.writestr(self.nomesOriginais[file], self.ARQUIVOS[file].save())
                    except:
                        print(f"ERRO AO SALVAR ARQUIVO: {file}")
                for file in SaveNaoMapeados:
                    try:
                        zip_out.writestr(file, self.ARQUIVOS_NAO_MAPEADOS[file]['bytes'])
                    except Exception as e: print(e)

            buffer.seek(0)
            return buffer.getvalue()

        elif type(self.caminho)==str or pasta!="":
            for file in self.ARQUIVOS.keys():
                try:
                    if file in ARQUIVOS_SAIDA: continue
                    if self.ARQUIVOS[file].ERROS:
                        print(f"IGNORANDO ARQUIVO '{file}' POIS TEM ERROS:")
                        print("     "+"\n     ".join(self.ERROS[file]['MSG']))
                        print("     "+"\n     ".join(self.ERROS[file]['DETALHES']))
                        continue
                    dados = self.ARQUIVOS[file].save()
                    if self.caminho == pasta and self.ARQUIVOS[file].hash == self.ARQUIVOS[file].gerarHash(): continue
                    if pasta=="":
                        caminho = self.nomesOriginais[file]
                    else:
                        caminho = os.path.join(pasta,self.nomesOriginais[file].split("/")[-1])
                        os.makedirs(pasta,exist_ok=True)
                    if type(dados)==bytes:
                        open(caminho,'wb').write(dados)
                    else:
                        open(caminho,'w').write(dados)
                except Exception as e:
                    print(f"ERRO AO SALVAR ARQUIVO: {file} | {e}")

        
        elif type(self.caminho)==bytes:
            buffer = BytesIO()
            with ZipFile(BytesIO(self.caminho), 'r') as zip_in:
                with ZipFile(buffer, 'w', ZIP_DEFLATED) as zip_out:
                    for file_name in zip_in.namelist():
                        try:
                            file = file_name.rsplit("/",1)[-1].lower().rsplit(".",1)[0]
                            if "-sem" in file_name.lower() and file in self.ARQUIVOS.keys():
                                if file in ARQUIVOS_SAIDA: continue
                                if self.ARQUIVOS[file].ERROS:
                                    print(f"IGNORANDO ARQUIVO '{file}' POIS TEM ERROS:")
                                    print("     "+"\n     ".join(self.ERROS[file]['MSG']))
                                    print("     "+"\n     ".join(self.ERROS[file]['DETALHES']))
                                    continue
                                zip_out.writestr(file_name, self.ARQUIVOS[file].save())
                            else:
                                zip_out.writestr(file_name, zip_in.read(file_name))
                        except Exception as e:
                            print(f"ERRO AO SALVAR ARQUIVO: {file_name} | {e}")
            buffer.seek(0)
            return buffer.getvalue()
        
        elif type(self.caminho)==ZipFile:
            buffer = BytesIO()
            zip_out = ZipFile(buffer, 'w', ZIP_DEFLATED)
            for file_name in self.caminho.namelist():
                try:
                    file = file_name.rsplit("/",1)[-1].lower().rsplit(".",1)[0]
                    if "-sem" in file_name.lower() and file in self.ARQUIVOS.keys():
                        if file in ARQUIVOS_SAIDA: continue
                        if self.ARQUIVOS[file].ERROS:
                            print(f"IGNORANDO ARQUIVO '{file}' POIS TEM ERROS:")
                            print("     "+"\n     ".join(self.ERROS[file]['MSG']))
                            print("     "+"\n     ".join(self.ERROS[file]['DETALHES']))
                            continue
                        zip_out.writestr(file_name, self.ARQUIVOS[file].save())
                    else:
                        zip_out.writestr(file_name, self.caminho.read(file_name))
                except Exception as e:
                    print(f"ERRO AO SALVAR ARQUIVO: {file_name} | {e}")
            return zip_out
    @property
    def usina_sem_reservatorio(self):
        usinas2 = []
        for usina in [x['Cod'] for x in self.ARQUIVOS['hidr'].blocos['hidr'].valores if x['Posto']!=0]:
            HIDR = self.ARQUIVOS['hidr'].blocos['hidr'].query({"Cod":usina})[0]
            TIPO = HIDR['Reg']
            VOLMIN = self.ARQUIVOS['dadger'].blocos['AC'].query({"Usina":usina,"Mnemonico":"VOLMIN"})
            VOLMAX = self.ARQUIVOS['dadger'].blocos['AC'].query({"Usina":usina,"Mnemonico":"VOLMAX"})
            VOLMIN  = VOLMIN[-1]['p1'] if self.hasValue(VOLMIN) else HIDR['Vol.min.(hm3)']
            VOLMAX  = VOLMAX[-1]['p1'] if self.hasValue(VOLMAX) else HIDR['Vol.Máx.(hm3)']
            if TIPO=="D" or VOLMIN==VOLMAX:
                usinas2.append(usina)
        return usinas2