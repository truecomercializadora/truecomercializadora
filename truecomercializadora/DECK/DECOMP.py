import os
from DECK.DC import prevs,regras, mlt, relato, volume_uhe, volume_sse, dadgnl, relgnl, inviab_unic
from DECK.DC.dadger import dadger
from DECK.NW import hidr, vazoes,postos,polinjus
from datetime import datetime,timedelta
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
from truecomercializadora.DECK.utils import UTILS
from dateutil.relativedelta import relativedelta
ARQUIVOS_MAPEADOS = {'dadger':dadger.DADGER,'vazoes':vazoes.VAZOES, 'postos':postos.POSTOS, 'polinjus':polinjus.POLINJUS, 'prevs':prevs.PREVS,'regras':regras.REGRAS, 'hidr':hidr.HIDR, 'mlt':mlt.MLT, 'relato':relato.RELATO, 'volume_uhe':volume_uhe.VOLUME_UHE, "volume_sse":volume_sse.VOLUME_SSE, 'dadgnl':dadgnl.DADGNL, 'outgnl':dadgnl.DADGNL, 'relgnl':relgnl.RELGNL, "inviab_unic":inviab_unic.INVIAB_UNIC}

ARQUIVOS_SAIDA = ['inviab_unic','relgnl','outgnl'] #ARQUIVOS QUE NÂO SERAO REESCRITOS AO SALVAR DECK
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
                if "vazoes" in file.rsplit("/",1)[-1].lower() and ".dat" not in file.lower(): continue
                self.nomesOriginais[nomeArq] = file
                if nomeArq in ARQUIVOS_MAPEADOS.keys():
                    file = os.path.join(self.caminho,file)
                    if 'dadger' in nomeArq: self.rev = file[-1]
                    self.ARQUIVOS[nomeArq] = ARQUIVOS_MAPEADOS[nomeArq](file)
                elif "." in file:
                    file = os.path.join(self.caminho,file)
                    self.ARQUIVOS_NAO_MAPEADOS[nomeArq] = {'bytes':open(file,'rb').read(),'caminho':file}

        elif type(self.caminho)==bytes: #PARA USAR BYTES DEVE-SE PASSAR A DATA DO DECK SE TIVER MAIS DE UM DECK NO ZIP
            with ZipFile(BytesIO(self.caminho)) as dados:
                 for file in [x for x in dados.namelist() if x.replace("\\",'/').split("/")[-1]!='']:
                    nomeArq = file.replace("\\",'/').rsplit("/",1)[-1].lower().rsplit(".",1)[0]
                    if 'polinjus.dat' in file.lower(): continue
                    if "vazoes" in file.rsplit("/",1)[-1].lower() and ".dat" not in file.lower(): continue
                    self.nomesOriginais[nomeArq] = file
                    if nomeArq in ARQUIVOS_MAPEADOS.keys():
                        if 'dadger' in nomeArq: self.rev = file[-1]
                        self.ARQUIVOS[nomeArq] = ARQUIVOS_MAPEADOS[nomeArq](dados.read(file))
                    elif "." in file:
                        self.ARQUIVOS_NAO_MAPEADOS[nomeArq] = {'bytes':dados.read(file),'caminho':file}
        elif type(self.caminho)==ZipFile: #PARA USAR ZIPFILE DEVE-SE PASSAR A DATA DO DECK SE TIVER MAIS DE UM DECK NO ZIP
            for file in [x for x in self.caminho.namelist() if x.replace("\\",'/').split("/")[-1]!='']:
                nomeArq = file.replace("\\",'/').rsplit("/",1)[-1].lower().rsplit(".",1)[0]
                if 'polinjus.dat' in file.lower():continue
                if "vazoes" in file.rsplit("/",1)[-1].lower() and ".dat" not in file.lower(): continue
                self.nomesOriginais[nomeArq] = file
                if nomeArq in ARQUIVOS_MAPEADOS.keys():
                    if 'dadger' in nomeArq: self.rev = file[-1]
                    self.ARQUIVOS[nomeArq] = ARQUIVOS_MAPEADOS[nomeArq](self.caminho.read(file))
                elif "." in file:
                    self.ARQUIVOS_NAO_MAPEADOS[nomeArq] = {'bytes':self.caminho.read(file),'caminho':file}

        dtSTR = self.ARQUIVOS['dadger'].blocos['DT'].valores[0]['stringDados'].split()
        self.data = datetime(int(dtSTR[-1]),int(dtSTR[-2]),int(dtSTR[-3]))
        self.dataDeck = (datetime(int(dtSTR[-1]),int(dtSTR[-2]),int(dtSTR[-3])) + timedelta(days=7)) + relativedelta(day = 1)

    def save(self,pasta=""):
        if type(self.caminho)==str or pasta!="":
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
                except:
                    print(f"ERRO AO SALVAR ARQUIVO: {file}")

        
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
                        except:
                            print(f"ERRO AO SALVAR ARQUIVO: {file_name}")


            buffer.seek(0)
            return buffer.getvalue()
        
        elif type(self.caminho)==ZipFile:
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
                except:
                    print(f"ERRO AO SALVAR ARQUIVO: {file_name}")
            return zip_out