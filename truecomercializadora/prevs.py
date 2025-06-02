'''
 Modulo para funcoes especificas de calculos envolvendo o arquivo prevs.
'''


from collections import defaultdict
import re

import numpy as np
from . import decomp
from . import utils_datetime
from . import utils_s3
import pandas as pd

def _get_prevs_obj(prevs_str: str) -> dict:
    """
    Retorna um dicionario das vazoes de cada um dos postos do prevs a partir do
     prevs.rv# em formato str.
    """
    
    if type(prevs_str) != str:
        raise Exception("'get_prevs_obj' can only receive a string."
                        "{} is not a valid input type".format(type(prevs_str)))
    if '     1    1' not in prevs_str:
        raise Exception("Input string does not seem to represent a prevs.rv# "
                        "string. Check the input")
        
    D = {
        int(line.split()[1]): [int(vazao) for vazao in line.split()[2:]]
            for line in prevs_str.splitlines()
            if line.split() != []
    }
    
    return D

def _get_vazoes_artificiais_bmonte(
    vazoes_prevs_bmonte: list,
    hidrograma_table: list,
    hidrograma_type: str,
    ano: int,
    mes: int) -> list:
    
    """
    Retorna a lista com as 6 vazoes artificiais de Belo Monte (posto 292).
     Considerando as ponderacoes de dias do mes em cada estagio (semana) do
     prevs.rv#
    """
    
    if type(vazoes_prevs_bmonte) != list:
        raise Exception("'get_vazoes_artificiais_bmonte' can only receive a list."
                        "{} is not a valid input type".format(type(vazoes_prevs_bmonte)))
    if len(vazoes_prevs_bmonte) != 6:
        raise Exception("'get_vazoes_artificiais_bmonte' can only receive a list of 6 integers"
                        "{} is not a valid input list".format(vazoes_prevs_bmonte))
    for vazao in vazoes_prevs_bmonte:
        if type(vazao) != int:
            raise Exception("'get_vazoes_artificiais_bmonte' can only receive a list of 6 integers"
                            " {} is not a valid input list".format(vazoes_prevs_bmonte))
    if type(hidrograma_table) != list:
        raise Exception("'get_vazoes_artificiais_bmonte' can only receive a list for input 'hidrograma_table'."
                        "{} is not a valid input type".format(type(hidrograma_table)))
    if hidrograma_type not in ['A', 'B', 'medio','true','ibama']:
        raise Exception("'get_vazoes_artificiais_bmonte' can only receive 'A', 'B' or 'medio' for input 'hidrograma_type'."
                        "{} is not a valid input".format(hidrograma_type))
    if type(ano) != int:
        raise Exception("'get_vazoes_artificiais_bmonte' can only receive an integer for input 'ano'."
                        "{} is not a valid input".format(ano))
    if mes not in range(1,13):
        raise Exception("'get_vazoes_artificiais_bmonte' can only receive an integer between 1 and 12 for input 'mes'."
                        "{} is not a valid input".format(mes))
    
    # Inferindo os dados necessarios
    estagios_decomp = decomp.get_estagios(ano=ano, mes=mes)

    if len(estagios_decomp)<6:
        mesCorrecao=mes+1 if mes!=12 else 1
        estagios_decomp.append(decomp.get_estagios(ano=ano, mes=mesCorrecao)[0])

    dias_mes_por_estagio = decomp.get_dias_do_mes_por_estagio(estagios_decomp)
    hidrograma_dict = {utils_datetime.get_br_abreviated_month_number(linha['mes']): linha[hidrograma_type] for linha in hidrograma_table}
    
    if mes == 12:
        mes_seguinte = 1
        mes_anterior = mes - 1
    elif mes == 1:
        mes_seguinte = mes + 1
        mes_anterior = 12
    else:
        mes_seguinte = mes + 1
        mes_anterior = mes - 1
    
    # Interando pelas semanas do prevs     
    L = []
    for i in range(6):
        n_dias = dias_mes_por_estagio[i]
        
        # Obtendo a vazao artificial considerando a ponderacao adequada do hidrograma         
        if i == 0:
            defluencia = (
                (7-n_dias)*hidrograma_dict.get(mes_anterior) + n_dias*hidrograma_dict.get(mes)
            )/7
        elif i != 0 and n_dias != 7:
            defluencia = (
                n_dias*hidrograma_dict.get(mes) + (7-n_dias)*hidrograma_dict.get(mes_seguinte)
            )/7
        elif n_dias == 0:
            defluencia = hidrograma_dict.get(mes_seguinte)
        else:
            defluencia = hidrograma_dict.get(mes)
         
        # Definindo a vazao artificial baseada na defluencia do hidrograma ponderado
        if vazoes_prevs_bmonte[i] < defluencia:
            L.append(0)
        elif vazoes_prevs_bmonte[i] > (defluencia + 13900):
            L.append(13900)
        else:
            L.append(int(vazoes_prevs_bmonte[i] - defluencia))
        
    return L

def _get_postos_artificiais_from_postos_table(postos_table:list) -> list:
    '''
    Retorna uma lista dos postos cujo tipo seja 'artificial' a partir da
     tabela de informacoes dos postos disponivel no google sheets
    '''
    
    if type(postos_table) != list:
        raise Exception("'get_postos_artificiais_from_postos_table' can only "
                        "receive a list. {} is not a valid input type".format(type(postos_table)))
    for posto in postos_table:
        if type(posto) != dict:
            raise Exception("'get_postos_artificiais_from_postos_table' can only receive a list of dict for postos_table"
                            "{} is not a valid input".format(postos_table[0]))
    
    lista_chaves = [
        'idPosto',
        'tipo',
        'nome',
        'bacia',
        'submercado',
        'resEquivalente',
        'produtibilidade',
        'vazSemana1',
        'vazSemana2',
        'idPostoRegredido',
        'idPostoJusante',
        'tempoViagem',
        'mltJan',
        'mltFev',
        'mltMar',
        'mltAbr',
        'mltMai',
        'mltJun',
        'mltJul',
        'mltAgo',
        'mltSet',
        'mltOut',
        'mltNov',
        'mltDez',
        'A0Jan',
        'A0Fev',
        'A0Mar',
        'A0Abr',
        'A0Mai',
        'A0Jun',
        'A0Jul',
        'A0Ago',
        'A0Set',
        'A0Out',
        'A0Nov',
        'A0Dez',
        'A1Jan',
        'A1Fev',
        'A1Mar',
        'A1Abr',
        'A1Mai',
        'A1Jun',
        'A1Jul',
        'A1Ago',
        'A1Set',
        'A1Out',
        'A1Nov',
        'A1Dez']
    
    if list(postos_table[0]) != lista_chaves:
        raise Exception('Tabela de informacoes dos postos nao parece estar coerente. '
                        'Verifique seu conteudo ou se ela foi alterada recentemente')
    
    return list(filter(lambda x: x['tipo'] == 'artificial', postos_table))

def add_regras_to_regras_prevs(dict_regras):
    dict_regras[119] =  {0: 'VAZ(118) / 0.800'}
    dict_regras.pop(118)
    
    return dict_regras

def _get_vazoes_artificiais(
    prevs_obj: dict,
    ano_prevs: int,
    mes_prevs: int,
    postos_artificiais: list,
    hidrograma_bmonte_table: list,
    hidrograma='medio',
    STAGE='prod') -> dict:
    
    '''
    Retorna um objeto (dicionario de listas). Contendo as vazoes de cada um dos
     postos artificiais nao incluidos no arquivo prevs mas necessarios para o calculo
     da ENA de cada submercado
    '''

    if type(prevs_obj) != dict:
        raise Exception("'_get_vazoes_artificiais' can only receive a dict for prevs_obj."
                        "{} is not a valid input type".format(type(prevs_obj)))
    if type(ano_prevs) != int:
        raise Exception("'_get_vazoes_artificiais' can only receive an integer for ano input."
                        "{} is not a valid input type".format(type(ano_prevs)))
    if mes_prevs not in range(1,13):
        raise Exception("'_get_vazoes_artificiais' can only receive an integer between 1,12 for mes input."
                        "{} is not a valid input type".format(mes_prevs))
    if type(postos_artificiais) != list:
        raise Exception("'_get_vazoes_artificiais' can only receive an list of dict as postos_artificiais"
                        "{} is not a valid input type".format(type(postos_artificiais)))
    if type(hidrograma_bmonte_table) != list:
        raise Exception("'_get_vazoes_artificiais' can only receive an list of dict as postos_artificiais"
                        "{} is not a valid input type".format(type(hidrograma_bmonte_table)))
    
    arquivo_regras = get_regras_prevs(f'true-datalake-{STAGE}')
    arquivo_regras = arquivo_regras.replace('SMAP','VAZ')
    dict_regras = parse_regras(arquivo_regras)
    dict_regras = add_regras_to_regras_prevs(dict_regras)
    dict_deps = extrai_postos_regra(dict_regras)

    D = {}
    df_prevs = pd.DataFrame(prevs_obj)
    df_base = df_prevs.drop(columns=[col for col in dict_regras.keys() if col in df_prevs.columns])
    vazoes = []

    df_artificiais = pd.DataFrame()
    # calculamos primeiro a 292 para calcular a 302 depois 
    df_base[292] = _get_vazoes_artificiais_bmonte(
        vazoes_prevs_bmonte=prevs_obj[288],
        hidrograma_table=hidrograma_bmonte_table,
        hidrograma_type=hidrograma,
        ano=mes_prevs,
        mes=mes_prevs
    )
    for posto in postos_artificiais:
        id_posto = posto['idPosto']
        calc_posto_artificial(id_posto,df_base,df_artificiais,dict_regras,dict_deps,'')

    return df_artificiais.to_dict(orient='list')

def get_vazoes_obj_from_prevs(
    prevs_str: str,
    postos_table: list,
    hidrograma_bmonte_table: list,
    ano_prevs:int,
    mes_prevs:int,
    hidrograma='medio',
    STAGE='prod') -> dict:
    
    '''
    Retorna um objeto (dicionario de listas). Contendo as vazoes de cada um dos
     postos, artificiais e naturais, a partir do prevs.rv# em formato string e considerando 
     as informacoes dos postos disponibilizadas atraves de uma lista de dicionarios, normalmente
     obtida consultando o google sheets.
    Alem disso a funcao tambem necessita dos dados para o calculo das vazoes de belo monte
     considerando seu hidrograma e as datas do ano.
    '''

    if type(prevs_str) != str:
        raise Exception("'get_vazoes_obj_from_prevs' can only receive a string for prevs_str."
                        "{} is not a valid input type".format(type(prevs_str)))
    if type(postos_table) != list:
        raise Exception("'get_vazoes_obj_from_prevs' can only receive a list of dict for postos_table."
                        "{} is not a valid input type".format(type(postos_table)))
    if type(hidrograma_bmonte_table) != list:
        raise Exception("'get_vazoes_obj_from_prevs' can only receive a list of dict for hidrograma_bmonte_table."
                        "{} is not a valid input type".format(type(hidrograma_bmonte_table)))
    if type(ano_prevs) != int:
        raise Exception("'get_vazoes_obj_from_prevs' can only receive an integer for ano input."
                        "{} is not a valid input type".format(type(ano_prevs)))
    if mes_prevs not in range(1,13):
        raise Exception("'get_vazoes_obj_from_prevs' can only receive an integer between 1,12 for mes input."
                        "{} is not a valid input type".format(mes_prevs))
    
    # Obtendo um objeto para as vazoes contidas no prevs    
    prevs_obj = _get_prevs_obj(prevs_str=prevs_str)
    
    # Obtendo um objeto para as vazoes artificiais
    postos_artificiais = _get_postos_artificiais_from_postos_table(postos_table)
    postos_artf_obj = _get_vazoes_artificiais(
        prevs_obj=prevs_obj,
        ano_prevs=ano_prevs,
        mes_prevs=mes_prevs,
        postos_artificiais=postos_artificiais,
        hidrograma_bmonte_table=hidrograma_bmonte_table,
        hidrograma=hidrograma,
        STAGE=STAGE
    )
    
    # Concatenando os objetos:
    return {**prevs_obj, **postos_artf_obj}

def get_regras_prevs(LAKE):
    """
        Baixa o arquivo regras_prevs mais atualizado do S3, que contém as regras dos postos artificiais do CV descritas.    
        Args:
            LAKE (str): nome do repositorio que sera utilizado (true-datalake-prod ou true-datalake-dev)
           
        Returns:
            str: String do arquivo lido do S3
    """

    return utils_s3.get_obj_from_s3(LAKE,'consume/ena/info/regras_prevs_v3.dat').decode('latin-1')

def extract_vaz(expression,keyword):
    """
        Efetua a leitura das formulas de cada uma das usinas a partir do keyword e da expressão escrita no arquivo e retorna os postos e os postos dos quais sao dependentes.
        Exemplo: {302: {288,292}} significa que o posto 302 depende dos postos 288 e 292 para ser calculado. 
        Args:
            Expression (str): Fórmula da usina 
            keyword(str): SMAP ou VAZ (SMAP implica leitura dos valores diretamente da saída do smap e VAZ implica leitura dos valores do previvaz. 
            Para os arquivos do prevs, a keyword será sempre VAZ).
           
        Returns:
            set: set contendo todas as usinas e suas dependencias 
    """
        
    chave = r"VAZ\((.*?)\)" if keyword == 'VAZ' else r"SMAP\((.*?)\)"
    numbers = []
    for match in re.finditer(r"VAZ\((.*?)\)", expression):
        number = match.group(1)
        if len(number.split(",")) == 2:
            number = number.split(",")[0]
        numbers.append(int(number))
    return set(numbers)
   
def extrai_postos_regra(dict_regras):
    """
        Faz a junção das expressões que possuem VAZ e SMAP no dicionario de dependencias
        Args:
            dict_regras (dict): dict contendo as regras de cada um dos postos 
        Returns:
            set: set contendo todas as usinas e suas dependencias 
    """
        
    dict_deps_smap = {i: extract_vaz(''.join(v.values()),'SMAP') for i, v in dict_regras.items()}
    dict_deps_vaz = {i: extract_vaz(''.join(v.values()),'VAZ') for i, v in dict_regras.items()}

    dict_deps = {}
    for key in dict_deps_vaz:
        dict_deps[key] = dict_deps_vaz[key].union(dict_deps_smap[key])
    
    return dict_deps

def parse_regras(regras):
    rows = [r for r in regras.splitlines() if r.strip() and not r.strip().startswith('#')]
    col_specs = [match.span() for match in re.finditer(' X+', rows[1])]
    last_row = next((i for i, r in enumerate(rows) if r.strip().startswith('9999')), len(rows))
    d = defaultdict(dict)
    for row in rows[2:last_row]:
        row, *comentarios = row.split('#')
        id_posto, mes = [int(row[s:e]) for s, e in col_specs[:2]]
        formula = row[col_specs[-1][0]:col_specs[-1][1]].strip().upper().replace(';', ',')
        d[id_posto][mes] = formula.upper().replace(';', ',')
    return dict(d)

def calc_posto_artificial(id_posto,df_base,df_artificiais,dict_regras,dict_deps,mes):
    """
        Calcula as vazoes das usinas artificiais atraves de chamadas recursivas a partir das usinas dependentes. 
        Args:
            id_posto (int): idPosto a ser calculado
            df_base (dataframe): df de vazoes dos postos que nao sao artificiais
            df_artificiais (dataframe): df de vazoes artificiais ja calculadas
            dict_regras (dict): dict contendo as regras de cada um dos postos 
            dict_deps (dict): dict contendo as dependencias entre os postos
            mes (int): mes em que sera utilizado o hidrograma de belo monte
        Returns:
            set: set contendo todas as usinas e suas dependencias 
    """

    if id_posto in df_base.columns or id_posto in df_artificiais.columns:
        return  

    if id_posto in dict_deps:
        for id_posto_requerido in dict_deps[id_posto]:
            calc_posto_artificial(id_posto_requerido,df_base,df_artificiais,dict_regras,dict_deps,mes)

    if id_posto in df_base.columns:
        return  

    if id_posto in dict_regras:
        scp = {
            'VAZ': lambda j, s=0: df_base[j].shift(-s).fillna(0),
            'SE': lambda cond, val_true, val_false: cond * val_true + (1 - cond) * val_false,
            'MIN': np.minimum,
            'MAX': np.maximum,
        }
        expr = dict_regras[id_posto]
        if 0 in expr:
            df_artificiais[id_posto] = eval(expr[0], {}, scp)
        elif id_posto == 292:
            df_artificiais[id_posto] = {m: eval(dict_regras[id_posto][m], {}, scp) for m in dict_regras[id_posto]}[mes]['natural']
        else:return 
        df_base[id_posto] = df_artificiais[id_posto] 
        
    else:
        print(f"Regra não definida para o posto: {id_posto}")
        return 
