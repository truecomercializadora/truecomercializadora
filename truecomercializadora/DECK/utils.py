import calendar
import struct
from datetime import datetime,timedelta
from truecomercializadora.DECK.DC.dadger import ac,rhe,rhq,rhv,hecm,VaVuVl #NAO APAGAR. É USADO NO EVAL

from workalendar.america import BrazilSaoPauloCity
from functools import lru_cache
import boto3
from calendar import monthrange
import ast
from dateutil.relativedelta import relativedelta
import hashlib
import pickle

OPERATORS = {
    '==': lambda x, y: x == y if not isinstance(x,str) else x.strip()==y.strip(),
    '!=': lambda x, y: x != y,
    '<': lambda x, y: x < y,
    '>': lambda x, y: x > y,
    '<=': lambda x, y: x <= y,
    '>=': lambda x, y: x >= y,
    'começa': lambda x, y: x.startswith(y),
    'termina': lambda x, y: x.endswith(y),
    'contem': lambda x, y: y in x,
}

def match_query(item, query):
    for key, condition in query.items():
        try:
            # Caso seja uma lista de condições → OR entre elas
            if isinstance(condition, list):
                if not any(
                    OPERATORS[op](item.get(key, ""), val)
                    for op, val in condition
                ):
                    return False

            # Caso seja uma tupla (operador, valor)
            elif isinstance(condition, tuple):
                op, val = condition
                if not OPERATORS[op](item.get(key, ""), val):
                    return False

            # Caso seja valor simples → assume "=="
            else:
                if not OPERATORS['=='](item.get(key, ""), condition):
                    return False
        except:
            return False
    return True

@lru_cache(maxsize=None)
def _obter_feriados_brasil(ano):
    """Obtém feriados do Brasil excluindo alguns específicos."""
    cal = BrazilSaoPauloCity()
    feriados = cal.holidays(ano)
    return set(
        f[0] for f in feriados
        if f[1] not in {
            "Anniversary of the city of São Paulo",
            "Constitutional Revolution of 1932"
        }
    )

@lru_cache(maxsize=None)
def _carregar_horas_patamares():
    """Carrega horas patamares do S3."""
    s3 = boto3.client('s3', region_name='sa-east-1')
    response = s3.get_object(
        Bucket='true-datalake-prod',
        Key='consume/carga/info/Patamares.csv'
    )['Body'].read().decode("latin-1")
    return ast.literal_eval(response)

class UTILS:
    @property
    def pd(self):
        try:
            import pandas as pd
            return pd.DataFrame(self.valores)
        except Exception as e: print(e)
    def gerarHash(self) -> str:
        valores = [self.blocos[x].valores for x in self.blocos]
        return hashlib.md5(pickle.dumps(valores)).hexdigest()

    def _to_datetime(self,ano,mes,dia=1):
        try:
            return datetime(int(ano),int(mes),int(dia))
        except:
            return datetime(9999,12,31)

    def hasValue(self,x):
        if type(x)!=list:
            return str(x).strip()!=""
        else:
            return len(x)!=0

    def query(self,query = {}):
        '''REALIZA QUERY NOS ITENS DO ARQUIVO ESCOLHIDO. A QUERY DEVE TER O FORMATO {"CHAVE":("QUERY","VALOR")}
        EX: {"Usina":(">=":3)} #Pega as usinas com valor maior ou igual a 3.
        As QUERYS possiveis são: ("==", "!=", "<", ">", "<=", ">=", "começa", "contem", "termina")
        Pode-se usar {"Usina":3} para a QUERY "=="
        
        '''
        return [item for item in self.valores if match_query(item, query)]

    def indexOf(self,linha):
        '''RETORNA O INDICE DE UMA LINHA NO ARQUIVO.'''
        if linha in self.valores:
            return self.valores.index(linha)
        else:
            return 0
        
    def insert(self,item,indice=None):
        if indice==None:
            return self.valores.append(item)
        else:
            return self.valores.insert(indice, item)
        


    def removerLinha(self,linha,replicarComentario=True,sliceCommentario=(0,-1)):
        '''Deleta a linha do bloco selecionado. Se replicarComentario for True, o comentario da linha anterior é replicado na linha seguinte, se ele for uma string, só é replicado caso essa string esteja no comentario da linha. (Util para não perder o comentario de incio de bloco)
        sliceCommentario seve para definir o tamanho do comentario a ser pego. Para pegar inteiro usa-se (0,None)
        '''
        try:
            if (type(replicarComentario)==bool and replicarComentario) or (replicarComentario in "".join(linha.get('_comentarioAnterior',[]))):
                index = self.indexOf(linha)
                self.valores[index+1]['_comentarioAnterior'] = linha['_comentarioAnterior'][sliceCommentario[0]:sliceCommentario[1]] + self.valores[index+1]['_comentarioAnterior']
        except: pass
        self.valores.remove(linha)
        print(f"REMOVENDO LINHA {linha}")
        return
    

    def _interpretarLinhaSplitMethod(self,bloco,linha,splitkey = None): #PARA O MODIF
        linhaDados = {}
        if len(bloco)==0:
            return {'stringDados':linha}
        
        i=0
        data = linha.strip().split(splitkey)
        for inicio, fim, tipo, chave in bloco:

            try:
                if inicio==fim==None:
                    try:
                        linhaDados[chave] = tipo(linhaDados)
                    except:
                        linhaDados[chave] = ""
                else:
                    try:
                        if chave == bloco[-1][-1]:
                            dados = " ".join(data[i:])
                        else:
                            dados = data[i]
                    except:
                        dados = ''
                    tipo = tipo.upper()
                    if tipo.startswith('A'):
                        linhaDados[chave] = dados
                    elif tipo.startswith('I'):
                        linhaDados[chave] = int(dados)
                    elif tipo.startswith('F'):
                        linhaDados[chave] = float(dados.replace(",","."))
                    elif tipo.startswith('Z'):
                        linhaDados[chave] = int(dados)
                    elif tipo.startswith('E'):
                        linhaDados[chave] = float(dados.replace(",","."))
                    else:
                        linhaDados[chave] = ""


            except:
                if "*" in tipo and linha[inicio-1:fim].strip()=="": #Um asterisco pode ser o campo em branco
                    linhaDados[chave] = linha[inicio-1:fim]
                elif "**" in tipo: #Dois asteriscos podem ser o campo pode ser qualquer valor
                        linhaDados[chave] = linha[inicio-1:fim]
                else:
                    linhaDados[chave] = "ERRO"
                    self.ERROS.append(f"Valor '{linha[inicio-1:fim]}' não está no padrão esperado: '{tipo}'")
            i+=1

        return linhaDados

    def _interpretarLinha(self,bloco,linha):
        linhaDados = {}
        if len(bloco)==0:
            return {'stringDados':linha}
        
        for inicio, fim, tipo, chave in bloco:
            try:
                if inicio==fim==0: continue
                elif inicio==fim==None:
                    try:
                        linhaDados[chave] = tipo(linhaDados)
                    except:
                        # import traceback;print(traceback.format_exc())
                        linhaDados[chave] = ""
                elif fim==None:
                    tipo = tipo.upper()
                    if tipo.startswith('A'):
                        linhaDados[chave] = linha.split(";")[inicio-1]
                    elif tipo.startswith('I'):
                        linhaDados[chave] = int(linha.split(";")[inicio-1])
                    elif tipo.startswith('F'):
                        linhaDados[chave] = float(linha.split(";")[inicio-1])
                    elif tipo.startswith('Z'):
                        linhaDados[chave] = int(linha.split(";")[inicio-1])
                        
                    else:
                        linhaDados[chave] = ""
                else:
                    tipo = tipo.upper()
                    if tipo.startswith('A'):
                        linhaDados[chave] = linha[inicio-1:fim]
                    elif tipo.startswith('I'):
                        linhaDados[chave] = int(linha[inicio-1:fim])
                    elif tipo.startswith('F'):
                        linhaDados[chave] = float(linha[inicio-1:fim])
                    elif tipo.startswith('Z'):
                        linhaDados[chave] = int(linha[inicio-1:fim])
                    elif tipo.startswith('E'):
                        linhaDados[chave] = float(linha[inicio-1:fim])
                    else:
                        linhaDados[chave] = ""


            except:
                if "*" in tipo and linha[inicio-1:fim].strip()=="":
                    linhaDados[chave] = linha[inicio-1:fim]
                elif "**" in tipo:
                        linhaDados[chave] = linha[inicio-1:fim]
                else:
                    linhaDados[chave] = "ERRO"
                    self.ERROS.append(f"Valor: '{linha[inicio-1:fim]}' não está no padrão esperado: '{tipo}'")

        MAXVALUE = max([0]+[x[1] for x in bloco if x[1]!=None and x[1]!=0])
        if MAXVALUE>0:
            if linha[MAXVALUE:].strip()!="":
                self.ERROS.append(f"Valor: '{linha[MAXVALUE:]}' após o limite do bloco na linha: '{linha}'")
                
        return linhaDados



    def _interpretarLinhaBinaria(self,bloco, linha,linhaDados = ""):
        if linhaDados == "":
            linhaDados = {}
        if not bloco:
            return {'stringDados': linha}

        for inicio, fim, tipo, chave in bloco:
            if inicio==fim==0: continue
            if inicio==fim==None:
                try:
                    linhaDados[chave] = tipo(linhaDados)
                except:
                    # import traceback;print(traceback.format_exc())
                    linhaDados[chave] = ""
            else:
                relevant_bytes = linha[inicio-1:fim]
                
                if tipo.startswith('A'):
                    # Decodificação de texto
                    linhaDados[chave] = relevant_bytes.decode("latin-1").rstrip()
                
                elif tipo.startswith('I'):
                    # Conversão de bytes para inteiro
                    linhaDados[chave] = int.from_bytes(relevant_bytes, byteorder='little', signed=True)
                
                elif tipo.upper().startswith('F'):
                    # Conversão de bytes para float
                    linhaDados[chave] = struct.unpack('<f', relevant_bytes)[0]
                
                else:
                    # Caso o tipo não seja tratado especificamente, retorna os bytes brutos
                    linhaDados[chave] = relevant_bytes
        return linhaDados



   

    def _saveLine(self,valor,tipo):
        '''TIPO F: float que preenche sempre as casas decimais com zero caso não tenha valores
           TIPO A: APenas o valor do texto original, ajustado para o tamanho do campo
           TIPO a: APenas o valor do texto original, sem ajuste para o tamanho do campo
           TIPO I: inteiro que preenche sempre os espaços á direita com zero caso não tenha preenchido o espaço total da variavel
           TIPO i: inteiro que preenche sempre os espaços á esquerda com zero caso não tenha preenchido o espaço total da variavel
           '''
        tipo = tipo.replace("*","")
        tamanho = int(tipo[1:].split(".")[0])
        if tipo.startswith('A'):  # Tipo de dado texto
            return valor.ljust(tamanho)
       
        if tipo.startswith('a'):  # Tipo de dado texto
            return valor
        
        elif tipo.startswith('I'):  # Tipo de dado inteiro
            return valor.rjust(tamanho)

        elif tipo.startswith('i'):  # Tipo de dado inteiro
            return valor.ljust(tamanho)


        elif tipo.startswith('Z'):
            z_len = int(tipo[1:])
            return valor.zfill(z_len)
        
        elif tipo.startswith('E'):
            e_val = float(valor)
            efmt = tipo[1:].split('.')
            edec = int(efmt[1])

            if e_val >= 1 or e_val == 0:
                if edec == 0:
                    str_value = "{:.1f}".format(e_val).rstrip("0").rstrip(".")
                else:
                    if edec > 3:
                        str_value = f"{e_val:.3f}"
                    else:
                        str_value = f"{e_val:.{edec}f}"
            else:
                str_value = f"{e_val:.{edec}E}"
                str_value = str_value.replace("E+0", "E+").replace("E-0", "E-")

            valor0,valor1 = str_value.split(".")
            valor1 = valor1.rstrip("0")
            str_value = f"{valor0}.{valor1 if valor1!='' else 0}"+("0" if len(valor1)<2 else "")
            return str_value.rjust(tamanho)[0:tamanho]


        elif tipo.startswith('F'):  # Tipo de dado float com ajuste de casas automatico
            minDecimal = int(tipo.split(".")[1])
            if valor.strip()!="":
                try:
                    valor0,valor1 = valor.split(".")
                except:
                    valor0,valor1 = valor,0
                try:
                    if int(valor1)==0:
                        if tipo.endswith("."):
                            valor = f"{valor0}."
                        else:
                            valor = f"{float(valor0):{tamanho}.{minDecimal}f}"
                    else:
                        if len(valor1)<minDecimal:
                            valor = f"{float(valor):{tamanho}.{minDecimal}f}"
                except:pass
            return valor.rjust(tamanho)
        else:
            return valor


    def _saveToFile(self,blocos,dictFormatCabecalho={}):
        stringFile = []
        for bloco in blocos: #SITUACAO PARA BLOCOS NAO MAPEADOS / SALVA APENAS A STRING
            if bloco.campos!=None and len(bloco.campos)==0:
                for row in bloco.valores:
                    if "_comentarioAnterior" in row.keys():
                        for item in row['_comentarioAnterior']:
                            stringFile.append(item)
                    stringFile.append(row['stringDados'])
            else:
                if len(bloco.cabecalho)>0:
                    stringFile.append(bloco.cabecalho.format(**dictFormatCabecalho))
                for row in bloco.valores:
                    if "_comentarioAnterior" in row.keys():
                        for item in row['_comentarioAnterior']:
                            stringFile.append(item)
                    if "_indice" in row.keys():
                        campos = bloco.camposList[row['_indice']]
                    else:
                        campos = bloco.campos
                    if campos==None: campos = bloco.camposList[-1]

                    if '_customBlock' in row.keys():
                        file,tipo = row['_customBlock'].split(".")
                        campos = eval(f"{file}.getBlocosMnemonico('{tipo}')")[0]

                    lastValue = [x for x in campos if x[0]!=None and x[0]!=0][-1][1]
                    output = [' '] * lastValue
                    for inicio, fim, tipo, chave in campos:
                        if inicio==fim==0 or inicio==fim==None: continue
                        output[inicio-1:fim] = self._saveLine(str(row[chave]),tipo)[0:fim-inicio+1]

                    result = ''.join(output).rstrip()
                    stringFile.append(result)
                try:
                    stringFile.append(bloco.endBlock)
                except: pass
        return "\n".join(stringFile).encode('latin-1')


    def _contar_dias_por_mes(self,data_inicio, data_fim):
        dias_por_mes = {}
        # Itera de mês em mês até alcançar o mês de fim
        while data_inicio <= data_fim:
            num_dias_no_mes = calendar.monthrange(data_inicio.year, data_inicio.month)[1]
            # Caso a data de fim esteja no mesmo mês
            if data_inicio.month == data_fim.month and data_inicio.year == data_fim.year:
                dias_por_mes[data_inicio.strftime("%m-%Y")] = (data_fim.day - data_inicio.day + 1)
                break
            
            # Caso contrário, contar os dias do mês atual
            if (data_inicio.month != data_fim.month) or (data_inicio.year != data_fim.year):
                dias_por_mes[data_inicio.strftime("%m-%Y")] = num_dias_no_mes - data_inicio.day + 1

            # Mudar para o próximo mês
            if data_inicio.month == 12:
                data_inicio = data_inicio.replace(year=data_inicio.year + 1, month=1, day=1)
            else:
                data_inicio = data_inicio.replace(month=data_inicio.month + 1, day=1)
        return dias_por_mes


    def _insertBytesValue(self,dest_bytes, value, formato, inicio, tamanho):
        if not formato or formato.strip() == "":
            return dest_bytes

        end = inicio - 1 + tamanho  # Calcular a posição final de uma vez
        if formato[0] == 'A':
            # Alinhamento de texto com espaço à direita
            padded_text = str(value or "").ljust(tamanho)
            result = padded_text.encode('iso-8859-1')
            dest_bytes[inicio - 1:end] = result

        elif formato[0] in ['I', 'Z']:
            if value is None:
                return dest_bytes
            result = struct.pack('<i', int(value))
            dest_bytes[inicio - 1:end] = result

        elif formato[0] in ['F', 'f']:
            if value is None:
                return dest_bytes
            result = struct.pack('<f', float(value))
            dest_bytes[inicio - 1:end] = result

        return dest_bytes



    def _saveToFileBytes(self,blocos):
        # Estimar o tamanho total de todos os blocos para alocar a memória de forma eficiente
        total_size = sum(bloco.size * len(bloco.valores) for bloco in blocos)
        result_bytes = bytearray(total_size)
        offset = 0

        for bloco in blocos:
            # Processa cada linha dentro do bloco
            
            for linha in bloco.valores:
                dest_bytes = bytearray(bloco.size)  # Alocar o bloco de destino para os dados
                for inicio, fim, tipo, chave in bloco.campos:
                    if inicio==fim==0 or inicio==fim==None: continue
                    if tipo == '':
                        continue
                    # Modificar o bytearray de destino com os valores dos campos
                    dest_bytes = self._insertBytesValue(dest_bytes, linha[chave], tipo[0], inicio, fim - inicio + 1)
                
                # Adiciona o bloco processado diretamente na variável result_bytes
                result_bytes[offset:offset + bloco.size] = dest_bytes
                offset += bloco.size

        return bytes(result_bytes)  # Retorna como bytes
    

    def _checkErros(self):
        dictErros = {}
        for file in self.ARQUIVOS:
            ERROS = []
            MSG = []
            if self.ARQUIVOS[file].ERROS:
                for bloco in self.ARQUIVOS[file].blocos:
                    for valor in  self.ARQUIVOS[file].blocos[bloco].valores:
                        if "ERRO" in valor.values():
                            mensagem = f"EXISTE UM ERRO NO ARQUIVO: '{file}', BLOCO: '{bloco}'. Algum valor não foi interpretado corretamente ou alguma linha/bloco podem estar deslocados"
                            print(mensagem)
                            MSG.append(mensagem)
                            break

                if any(['após o limite do bloco na linha' in x for x in self.ARQUIVOS[file].ERROS]):
                    mensagem = f"EXISTE VALORES APÓS O LIMITE DO BLOCO NO '{file}'. ISSO PODE INDICAR UM BLOCO/LINHA DESLOCADA"
                    MSG.append(mensagem)
                    print(mensagem)

                ERROS += self.ARQUIVOS[file].ERROS

            if MSG or ERROS:
                dictErros[file] = {"MSG":MSG, "DETALHES":ERROS}
        return dictErros

    codificacoes_para_tentar = ['utf-8', 'cp1252', 'latin1']
    
    def abrir_arquivo_com_codificacao_automatica(self):
        codificacoes_para_tentar = ['utf-8', 'cp1252', 'latin1']
        for codificacao in codificacoes_para_tentar:
            try:
                if type(self.caminho)==bytes:
                    self.originalBytes = self.caminho
                else:
                    with open(self.caminho, 'rb') as f:
                        self.originalBytes = f.read()
                return self.originalBytes.decode(codificacao).splitlines()
            except:
                pass

    class MesOperativo:
        def __init__(self, data: datetime):
            self.Ano: int = data.year
            self.Mes: int = data.month
            self.SemanasOperativas = []
            self.Inicio = None
            self.Fim = None
            self.DiasMes2 = None
            self.MesSeguinte = None
            self.AnoSeguinte = None
            self.Estagios = None

            self.horas_patamares = _carregar_horas_patamares()
            self.feriados = _obter_feriados_brasil(self.Ano)

            self.create_semanal()

        def getDiasMes(self):
            """RETORNA OS DIAS DENTRO DO MES PARA CADA SEMANA e o TOTAL DE DIAS DO MES"""
            DIAS = {}
            for semana in self.SemanasOperativas: #CONSTROI GERACAO DO MES 1
                if semana['Inicio'].month == self.Mes or semana['Fim'].month == self.Mes:
                    dataSemanaInic = semana['Inicio']+relativedelta(day=1)
                    dataSemanaFim = semana['Fim']+relativedelta(day=1)
                    dataRef = datetime(self.Ano,self.Mes,1)
                    if dataSemanaInic<dataRef:
                        dias = semana['Fim'].day
                    elif dataSemanaFim>dataRef:
                        dias = ((semana['Inicio']+relativedelta(months=1)+relativedelta(day=1)) - semana['Inicio']).days
                    else:
                        dias = 7
                    DIAS[semana['Inicio']] = dias
            TOTAL_DIAS = (dataRef+relativedelta(months=1)-relativedelta(days=1)).day
            return DIAS,TOTAL_DIAS
        
        def get_horas_patamares(self, ini: datetime, fim: datetime):
            """Calcula a soma das horas de patamares entre duas datas."""
            p1 = p2 = p3 = 0
            dt = ini
            feriados_ano = self.feriados  # já como set

            while dt <= fim:
                ano_data = dt.year
                mes_data = dt.month

                if dt.weekday() in (5, 6) or dt.date() in feriados_ano:
                    pat = self.horas_patamares[ano_data][mes_data][1]
                else:
                    pat = self.horas_patamares[ano_data][mes_data][0]
                p1 += pat[2]
                p2 += pat[1]
                p3 += pat[0]
                dt += timedelta(days=1)

            return p1, p2, p3

        def _SemanaOperativa(self, inicio: datetime, fim: datetime):
            """Cria dicionário representando uma semana operativa."""
            pat = self.get_horas_patamares(inicio, fim)
            return {
                "Inicio": inicio,
                "Fim": fim,
                "HorasPat1": pat[0],
                "HorasPat2": pat[1],
                "HorasPat3": pat[2]
            }

        def create_semanal(self):
            """Cria as semanas operativas do mês."""
            dt = datetime(self.Ano, self.Mes, 1)
            while dt.weekday() != 5:  # Sábado
                dt -= timedelta(days=1)
            self.Inicio = dt

            dt += timedelta(days=6)

            while dt.month == self.Mes:
                self.SemanasOperativas.append(
                    self._SemanaOperativa(dt - timedelta(days=6), dt)
                )
                dt += timedelta(days=7)

            # Fim do mês
            last_day = monthrange(self.Ano, self.Mes)[1]
            fim_mes = datetime(self.Ano, self.Mes, last_day)

            if dt.day == 7:
                inicio = (datetime(self.Ano, self.Mes, 1) + timedelta(days=31)).replace(day=1)
                fim = (inicio + timedelta(days=31)).replace(day=1) - timedelta(days=1)
                self.SemanasOperativas.append(self._SemanaOperativa(inicio, fim))
                self.Fim = dt - timedelta(days=7)
                self.DiasMes2 = 0
            else:
                self.SemanasOperativas.append(
                    self._SemanaOperativa(dt - timedelta(days=6), dt)
                )

                inicio = dt + timedelta(days=1)
                fim = (datetime(self.Ano, self.Mes, 1) + timedelta(days=62)).replace(day=1) - timedelta(days=1)
                self.SemanasOperativas.append(self._SemanaOperativa(inicio, fim))
                self.Fim = dt
                self.DiasMes2 = dt.day

            self.MesSeguinte = dt.month
            self.AnoSeguinte = dt.year
            self.Estagios = len(self.SemanasOperativas) - 1