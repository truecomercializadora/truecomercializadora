"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo sistema
"""
import io
import pandas as pd
import re

from . import utils_datetime
from . import utils_files

def get_mercado_energia_total_str(sistema_str: str) -> str:
    """
    Retorna a substring correspondente ao bloco de mercado de energia total de um
     arquivo sistema.dat em seu formato string.
    """
    if type(sistema_str) != str:
        raise Exception("'get_mercado_energia_total' can only receive a string."
                        "{} is not a valid input type".format(type(sistema_str)))

    if 'MERCADO DE ENERGIA TOTAL' not in sistema_str:
        raise Exception("Input string does not seem to represent a sistema.dat "
                        "string. Check the input")

    begin = 'MERCADO DE ENERGIA TOTAL'
    end = ' GERACAO DE USINAS NAO SIMULADAS'
    mercado_energia_total = utils_files.select_document_part(sistema_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    mercado_energia_total_str = '\n'.join(mercado_energia_total.splitlines()[:-1])

    return mercado_energia_total_str

def get_mercado_energia_total_dict(mercado_energia_total_str: str):
    '''
    Retorna um objeto contendo os valores de carga, distribuidos em ano, submercado
     e mes, do bloco Mercado de Energia Total de um sistema.dat

     : mercado_energia_total_str deve ser a string obtida atraves da funcao
      'get_mercado_energia_total()'
    '''

    if type(mercado_energia_total_str) != str:
        raise Exception("'get_mercado_energia_total_dict' can only receive a string."
                        "{} is not a valid input type".format(type(mercado_energia_total_str)))

    file_lines = mercado_energia_total_str.splitlines()

    # Dividindo a string em submercados
    submercados =  {
        'SE': file_lines[4:10],
        'S': file_lines[11:17],
        'NE': file_lines[18:24],
        'N': file_lines[25:31]
    }

    # Escrevendo cada submercado de forma iterativa para um dicionario
    D = {}
    for submercado in submercados:
        d = {}
        for row in submercados[submercado]:
            values = {
                'jan':row[5:15].strip(),
                'fev':row[15:23].strip(),
                'mar':row[23:31].strip(),
                'abr':row[31:39].strip(),
                'mai':row[39:47].strip(),
                'jun':row[47:55].strip(),
                'jul':row[55:63].strip(),
                'ago':row[63:71].strip(),
                'set':row[71:79].strip(),
                'out':row[79:87].strip(),
                'nov':row[87:95].strip(),
                'dez':row[95:].strip(),     
            }
            d.update({row[:5].strip(): values})
        D.update({submercado: d})
    return D

def _get_mercado_energia_formated_line(
    df_submercado: pd.DataFrame,
    format_type: str,
    begin_idx: int,
    submercado_number: int=None) -> str:

    """
    Retorna uma string correspondente a linha desejada do bloco Mercado de Energia
     Total, baseado no dataframe do submercado, o tipo de formato da linha o indice
     inicial da linha do bloco e, se necessario, qual o submercado
    """

    if type(df_submercado) != pd.DataFrame:
        raise Exception("'_get_mercado_energia_formated_line' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_submercado)))
    if format_type not in ['A', 'B', 'C']:
        raise Exception("'_get_mercado_energia_formated_line' can only receive 'A', 'B' or 'C' as format_type."
                        "{} is not a valid input type".format(type(format_type)))
    if type(begin_idx) != int:
        raise Exception("'_get_mercado_energia_formated_line' can only receive line index as integer."
                        "{} is not a valid input type".format(type(begin_idx)))

    if format_type == 'A':
        line_format = "   {}\n{}    {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}. \n"
        return line_format.format(submercado_number,
            df_submercado.iloc[begin_idx]['data'].year,
            df_submercado.iloc[begin_idx]['valor'],
            df_submercado.iloc[begin_idx+1]['valor'],
            df_submercado.iloc[begin_idx+2]['valor'],
            df_submercado.iloc[begin_idx+3]['valor'],
            df_submercado.iloc[begin_idx+4]['valor'],
            df_submercado.iloc[begin_idx+5]['valor'],
            df_submercado.iloc[begin_idx+6]['valor'],
            df_submercado.iloc[begin_idx+7]['valor'],
            df_submercado.iloc[begin_idx+8]['valor'],
            df_submercado.iloc[begin_idx+9]['valor'],
            df_submercado.iloc[begin_idx+10]['valor'],
            df_submercado.iloc[begin_idx+11]['valor']        
        )
    if format_type == 'B':
        line_format = "{}    {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}. \n"
        return line_format.format(
            df_submercado.iloc[begin_idx]['data'].year,
            df_submercado.iloc[begin_idx]['valor'],
            df_submercado.iloc[begin_idx+1]['valor'],
            df_submercado.iloc[begin_idx+2]['valor'],
            df_submercado.iloc[begin_idx+3]['valor'],
            df_submercado.iloc[begin_idx+4]['valor'],
            df_submercado.iloc[begin_idx+5]['valor'],
            df_submercado.iloc[begin_idx+6]['valor'],
            df_submercado.iloc[begin_idx+7]['valor'],
            df_submercado.iloc[begin_idx+8]['valor'],
            df_submercado.iloc[begin_idx+9]['valor'],
            df_submercado.iloc[begin_idx+10]['valor'],
            df_submercado.iloc[begin_idx+11]['valor']        
        )    
    elif format_type == 'C':
        line_format = "POS     {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}. \n"
        return line_format.format(
        df_submercado.iloc[begin_idx]['valor'],
        df_submercado.iloc[begin_idx+1]['valor'],
        df_submercado.iloc[begin_idx+2]['valor'],
        df_submercado.iloc[begin_idx+3]['valor'],
        df_submercado.iloc[begin_idx+4]['valor'],
        df_submercado.iloc[begin_idx+5]['valor'],
        df_submercado.iloc[begin_idx+6]['valor'],
        df_submercado.iloc[begin_idx+7]['valor'],
        df_submercado.iloc[begin_idx+8]['valor'],
        df_submercado.iloc[begin_idx+9]['valor'],
        df_submercado.iloc[begin_idx+10]['valor'],
        df_submercado.iloc[begin_idx+11]['valor']        
    )

def _write_bloco_submercado(df_submercado: pd.DataFrame, submercado_number: int) -> bytes:

    """
    Retorna uma string correspondente a sessao do submercado dentro do bloco de Mercado
     de Energia Total.
    """

    if type(df_submercado) != pd.DataFrame:
        raise Exception("'_write_bloco_submercado' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_submercado)))
    if submercado_number not in [1,2,3,4]:
        raise Exception("'_write_bloco_submercado' can only integers between [1,4] for submercado_number."
                        "{} is not a valid input type".format(type(submercado_number)))

    master_io = io.BytesIO()
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='A',begin_idx=0, submercado_number=submercado_number).encode('latin-1'))
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='B',begin_idx=12).encode('latin-1'))
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='B',begin_idx=24).encode('latin-1'))
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='B',begin_idx=36).encode('latin-1'))
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='B',begin_idx=48).encode('latin-1'))
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='C',begin_idx=48).encode('latin-1'))
    return master_io.getvalue().decode()


def write_mercado_energia(
        df_sudeste: pd.DataFrame,
        df_sul: pd.DataFrame,
        df_nordeste: pd.DataFrame,
        df_norte: pd.DataFrame) -> str:
    '''
    Escreve o bloco Mercado de Energia Total de um arquivo sistema.dat a partir
    dos dataframes de carga dos 4 submercados.
    '''

    if type(df_sudeste) != pd.DataFrame:
        raise Exception("'write_mercado_energia' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_sudeste)))
    if type(df_sul) != pd.DataFrame:
        raise Exception("'write_mercado_energia' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_sul)))
    if type(df_nordeste) != pd.DataFrame:
        raise Exception("'write_mercado_energia' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_nordeste)))
    if type(df_norte) != pd.DataFrame:
        raise Exception("'write_mercado_energia' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_norte)))

    master_io = io.BytesIO()
    master_io.write(" MERCADO DE ENERGIA TOTAL\n".encode("latin-1"))
    master_io.write(" XXX\n".encode("latin-1"))
    master_io.write("       XXXJAN. XXXFEV. XXXMAR. XXXABR. XXXMAI. XXXJUN. XXXJUL. XXXAGO. XXXSET. XXXOUT. XXXNOV. XXXDEZ.\n".encode('latin-1'))

    bloco_sudeste = _write_bloco_submercado(df_sudeste, 1)
    bloco_sul = _write_bloco_submercado(df_sul, 2)
    bloco_nordeste = _write_bloco_submercado(df_nordeste, 3)
    bloco_norte = _write_bloco_submercado(df_norte, 4)

    output_str = master_io.getvalue().decode() + bloco_sudeste + bloco_sul + bloco_nordeste + bloco_norte
    return output_str.strip()

# =============================== NAO SIMULADAS ================================
def get_nao_simuladas_str(sistema_str: str) -> str:
    """
    Retorna a substring correspondente ao bloco de usinas nao simuladas
     do arquivo sistema.dat em seu formato string.
    """
    if type(sistema_str) != str:
        raise Exception("'get_usinas_nao_simuladas_str' can only receive a string."
                        "{} is not a valid input type".format(type(sistema_str)))

    if 'GERACAO DE USINAS NAO SIMULADAS' not in sistema_str:
        raise Exception("Input string does not seem to represent a sistema.dat "
                        "string. Check the input")

    begin = ' GERACAO DE USINAS NAO SIMULADAS'
    begin_idx = sistema_str.find(begin)
    
    # eliminando as linhas antes e depois dos dados     
    nao_simuladas_str = '\n'.join(sistema_str[begin_idx:].splitlines()[:-1])

    return nao_simuladas_str

def get_nao_simuladas_dict(nao_simuladas_str: str):
    '''
    Retorna um objeto contendo os valores despacho de cada submercado
     tipo de usina e mes, do bloco Usinas Nao Simuladas de um sistema.dat

     : get_nao_simuladas_dict deve ser a string obtida atraves da funcao
      'get_nao_simuladas_str()'
    '''

    if type(nao_simuladas_str) != str:
        raise Exception("'get_nao_simuladas_dict' can only receive a string."
                        "{} is not a valid input type".format(type(nao_simuladas_str)))

    file_lines = nao_simuladas_str.splitlines()
    
    submercados = {
        'SE':file_lines[3:51],
        'S':file_lines[51:99],
        'NE':file_lines[99:147],
        'N':file_lines[147:195]
    }

    # Escrevendo cada submercado em um dicionario
    nao_simuladas = {}
    for submercado in submercados:
        D = {}
        bloco_usinas = {
            'PCH':submercados[submercado][1:6],
            'PCT':submercados[submercado][7:12],
            'EOL':submercados[submercado][13:18],
            'UFV':submercados[submercado][19:24],
            'PCH MMGD':submercados[submercado][25:30],
            'PCT MMGD':submercados[submercado][31:36],
            'EOL MMGD':submercados[submercado][37:42],
            'UFV MMGD':submercados[submercado][43:49],

        }
        
        # Adicionando cada bloco de tipo de usina
        for bloco in bloco_usinas:
            d = {}
            
            # Iterando pelos anos do bloco
            for row in bloco_usinas[bloco]:
                values = {
                    'jan':row[5:15].strip(),
                    'fev':row[15:23].strip(),
                    'mar':row[23:31].strip(),
                    'abr':row[31:39].strip(),
                    'mai':row[39:47].strip(),
                    'jun':row[47:55].strip(),
                    'jul':row[55:63].strip(),
                    'ago':row[63:71].strip(),
                    'set':row[71:79].strip(),
                    'out':row[79:87].strip(),
                    'nov':row[87:95].strip(),
                    'dez':row[95:].strip(),     
                }
                d.update({row[:5].strip(): values})
            D.update({bloco: d})
        nao_simuladas.update({submercado: D})
    
    return nao_simuladas


def get_nao_simuladas_df(nao_simuladas_dict: dict) -> pd.DataFrame:
    '''
    Retorna um DataFrame a partir do dicionario interpretado das geracoes das usinas nao simuladas
     : nao_simuladas_dict deve ser o dict obtido atraves da funcao
     'get_nao_simuladas_dict()'
    '''
    
    if type(nao_simuladas_dict) != dict:
        raise Exception("'get_nao_simuladas_df' can only receive a dictionary."
                        "{} is not a valid input type".format(type(nao_simuladas_dict)))
    
    # Iterando pelas chaves do dicionario e construindo linhas de um dataframe
    L = []
    for submercado, submercados_obj in nao_simuladas_dict.items():
        for usina, usinas_obj in submercados_obj.items():
            for ano, anos_obj in usinas_obj.items():
                for mes, value in anos_obj.items():
                    row = {
                        'submercado': submercado,
                        'tipo': usina,
                        'ano': int(ano), 
                        'mes': utils_datetime.get_br_abreviated_month_number(mes),
                        'geracao': value
                    }
                    L.append(row)
    return pd.DataFrame(L)



def carga_df(sistema):
    '''
    Retorna um dataframe com o bloco carga do sistema. Tem como entrada a string do sistema.dat
    '''
    dict={0:"SUDESTE",1:"SUL",2:"NORDESTE",3:"NORTE"}
    sistema=sistema.splitlines()
    carga=[]
    for item in sistema[92:120]:
        teste=[item[0:5],item[8:14],item[16:22],item[24:30],item[32:38],item[40:46],item[48:54],item[56:62],item[64:70],item[72:78],item[80:86],item[88:94],item[96:102]]
        for i in range(len(teste)):
            if teste[i].strip()=="":
                teste[i]=0
            else: teste[i]=teste[i].strip()
        carga.append(teste)
    df_final=pd.DataFrame()
    for i in range(4):
        carga1={}
        for item in carga[i*7+1:7*i+7]:
            carga1[dict[i],item[0]]=item[1:]
            df=pd.DataFrame(carga1,index=[i+1 for i in range(12)]).T
        df_final=df_final.append(df)
    df_final=df_final.astype({i+1:float for i in range(12)})
    df_final=df_final.astype({i+1:int for i in range(12)})
    return(df_final)

def intercambio_df(sistema):
    '''
    Retorna um dataframe com o bloco intercambio do sistema. Tem como entrada a string do sistema.dat
    '''
    dict={0:"1-2",1:"2-1",2:"1-11",3:"11-1",4:"3-11",5:"11-3",6:"4-11",7:"11-4",8:"1-3",9:"3-1",10:"1-4",11:"4-1",}
    sistema=sistema.splitlines()
    intercambio=[]
    for item in sistema[16:88]:
        teste=[item[0:5],item[8:14],item[16:22],item[24:30],item[32:38],item[40:46],item[48:54],item[56:62],item[64:70],item[72:78],item[80:86],item[88:94],item[96:102]]
        for i in range(len(teste)):
            if teste[i].strip()=="":
                teste[i]=0
            else: teste[i]=teste[i].strip()
        intercambio.append(teste)
    df_final=pd.DataFrame()
    for i in range(12):
        carga1={}
        for item in intercambio[i*6+1:(i+1)*6]:
            carga1[dict[i],item[0]]=item[1:]
            df=pd.DataFrame(carga1,index=[i+1 for i in range(12)]).T
        df_final=df_final.append(df)
    df_final=df_final.astype({i+1:float for i in range(12)})
    df_final=df_final.astype({i+1:int for i in range(12)})
    return df_final

def pequenas_df(sistema):
    '''
    SE POSSÍVEL, USAR: 'pequenas_df_sem_mmgd'

    Retorna um dataframe com o bloco pequenas do sistema. Tem como entrada a string do sistema.dat
    '''
    dict={0:"1",1:"1",2:"1",3:"1",4:"2",5:"2",6:"2",7:"2",8:"3",9:"3",10:"3",11:"3",12:"4",13:"4",14:"4",15:"4"}
    sistema=sistema.splitlines()
    intercambio=[]
    for item in sistema[124:220]:
        teste=[item[0:5],item[8:14],item[16:22],item[24:30],item[32:38],item[40:46],item[48:54],item[56:62],item[64:70],item[72:78],item[80:86],item[88:94],item[96:102]]
        for i in range(len(teste)):
            if teste[i].strip()=="":
                teste[i]=0
            else: teste[i]=teste[i].strip()
        intercambio.append(teste)
    df_intermediario=pd.DataFrame()
    for i in range(16):
        carga1={}
        for item in intercambio[i*6+1:(i+1)*6]:
            carga1[dict[i],item[0]]=item[1:]
            df=pd.DataFrame(carga1,index=[i+1 for i in range(12)]).T
        df_intermediario=df_intermediario.append(df)
    df_intermediario=df_intermediario.astype({i+1:float for i in range(12)})
    df_intermediario=df_intermediario.astype({i+1:int for i in range(12)})
    dict={1:"SUDESTE",2:"SUL",3:"NORDESTE",4:"NORTE"}
    inicio=int(list(df_intermediario.index)[0][1])
    fim=int(list(df_intermediario.index)[-1][1])
    df_final=pd.DataFrame()
    for i in range(4):
        for j in range(fim-inicio+1):
            df_2=pd.DataFrame(df_intermediario[df_intermediario.index.isin( [(str(i+1), str(inicio+j))])].sum()).T
            df_2["ANO"]=inicio+j
            df_2["SUBSISTEMA"]=dict[i+1]
            df_final=df_final.append(df_2)
    df_final=df_final.set_index(["SUBSISTEMA","ANO"])
    return df_final


def pequenas_df_sem_mmgd(sistema):
    '''
    Retorna um dataframe com o bloco pequenas do sistema sem MMGD. Tem como entrada a string do sistema.dat
    '''
    padrao_nao_simuladas = r'GERACAO DE USINAS NAO SIMULADAS.*'
    resultado_nao_simuladas = re.search(padrao_nao_simuladas, sistema, re.DOTALL)
    arquivo_nao_simuladas = resultado_nao_simuladas.group(0).strip()
    
    padrao_tamanhos_meses = r'\n(\s*)(.*?JAN.)(\s.*?FEV.)(\s.*?MAR.)(\s.*?ABR.)(\s.*?MAI.)(\s.*?JUN.)(\s.*?JUL.)(\s.*?AGO.)(\s.*?SET.)(\s.*?OUT.)(\s.*?NOV.)(\s.*?DEZ.)\s'
    resultado_tamanhos_meses = re.search(padrao_tamanhos_meses, arquivo_nao_simuladas)
    tamanho_colunas = dict()
    sobressalente = 0
    for i in range(1, 14):
        if i == 1:
            # Espaço antes de Janeiro
            sobressalente = len(resultado_tamanhos_meses.group(i)) - 4 # len anual
            tamanho_colunas[i - 1] = 4 # len anual
        elif i == 2:
            # Janeiro
            tamanho_colunas[i - 1] = sobressalente + len(resultado_tamanhos_meses.group(i))
        else:
            # Meses restantes
            tamanho_colunas[i - 1] = len(resultado_tamanhos_meses.group(i))
    
    padrao_dados_nao_simuladas = r'(?:DEZ)(.*)(?:\s*999\s*)'
    resultado_dados_nao_simuladas = re.search(padrao_dados_nao_simuladas, arquivo_nao_simuladas, re.DOTALL)
    arquivo_dados_nao_simuladas = resultado_dados_nao_simuladas.group(1).strip()
    intercambio = list()
    flag_ignorar_mmgd = 0
    for item in arquivo_dados_nao_simuladas.splitlines()[1:]: # [1:] -> eliminar o '.' do 'DEZ.'
        lista_itens = list()
        elementos = re.split(r'\s{3,}', item)
        if elementos[0] == '': # cabeçalhos
            lista_itens = elementos[1:] + [0 for i in range(11)]
        else: # dados
            soma_tamanho_anterior = 0
            for tamanho in tamanho_colunas.values():
                valor = item[soma_tamanho_anterior: soma_tamanho_anterior + tamanho].strip()
                if valor == "":
                    valor = 0
                soma_tamanho_anterior += tamanho
                lista_itens.append(valor)
        for i in lista_itens:
            try:
                if 'MMGD' in i: # Não extrair os dados da MMGD
                    flag_ignorar_mmgd = 6
                    break
            except: pass
        if flag_ignorar_mmgd == 0:
            intercambio.append(lista_itens)
        else:
            flag_ignorar_mmgd -= 1

    dicio={0:"1",1:"1",2:"1",3:"1",4:"2",5:"2",6:"2",7:"2",8:"3",9:"3",10:"3",11:"3",12:"4",13:"4",14:"4",15:"4"}
    df_intermediario=pd.DataFrame()
    for i in range(16):
        carga1={}
        for item in intercambio[i*6+1:(i+1)*6]:
            carga1[dicio[i],item[0]]=item[1:]
            df=pd.DataFrame(carga1,index=[i+1 for i in range(12)]).T
        df_intermediario=df_intermediario.append(df)
    df_intermediario=df_intermediario.astype({i+1:float for i in range(12)})
    df_intermediario=df_intermediario.astype({i+1:int for i in range(12)})
    dicio={1:"SUDESTE",2:"SUL",3:"NORDESTE",4:"NORTE"}
    inicio=int(list(df_intermediario.index)[0][1])
    fim=int(list(df_intermediario.index)[-1][1])
    df_final=pd.DataFrame()
    for i in range(4):
        for j in range(fim-inicio+1):
            df_2=pd.DataFrame(df_intermediario[df_intermediario.index.isin( [(str(i+1), str(inicio+j))])].sum()).T
            df_2["ANO"]=inicio+j
            df_2["SUBSISTEMA"]=dicio[i+1]            
            df_final=df_final.append(df_2)
    df_final=df_final.set_index(["SUBSISTEMA","ANO"])
    return df_final


def tabela_diferencas(df1,df2):
    '''
    Retorna um dataframe com a diferença entre dois dataframes resultantes das funções 'bloco'_df, com o 'bloco' podendo ser 'pequenas','intercambio' ou 'carga'.
    '''
    df_diff=df1-df2
    index=list(df_diff.index)
    teste2=[]
    for item in index:
        teste=0
        for item2 in df_diff.loc[item]:
            if item2==0 or pd.isna(item2):
                teste=teste+1
        if teste==len(df_diff.columns):
            continue
        teste2.append(item)

    df_1=df1.loc[list(df_diff.loc[teste2].index)]
    df_2=df2.loc[list(df_diff.loc[teste2].index)]

    return (df_diff.loc[teste2]).round().astype(int),df_1.round().astype(int),df_2.round().astype(int)
