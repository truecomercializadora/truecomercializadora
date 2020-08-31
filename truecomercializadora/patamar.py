"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo patamar
"""

import pandas as pd

from . import utils_datetime
from . import utils_files

# ============================= NUMERO PATAMARES ===============================
def get_numero_patamares(patamar_str: str) -> int:
    """
    Retorna o inteiro correspondente ao numero de patamares definido
     no arquivo 
    """
    if type(patamar_str) != str:
        raise Exception("'get_numero_patamares' can only receive a string."
                        "{} is not a valid input type".format(type(patamar_str)))

    if ' NUMERO DE PATAMARES' not in patamar_str:
        raise Exception("Input string does not seem to represent a sistema.dat "
                        "string. Check the input")

   
    # Obtendo os patamares com o pressuposto dele estar na terceira linha
    #  do documento
    return int(patamar_str.splitlines()[2].strip())

# ============================= DURACAO PATAMARES ==============================
def get_duracao_patamares_str(patamar_str: str) -> str:
    """
    Retorna a substring correspondente ao bloco de duracao dos patamares
     de um arquivo patamar.dat em seu formato string.
    """
    if type(patamar_str) != str:
        raise Exception("'get_duracao_patamares_str' can only receive a string."
                        "{} is not a valid input type".format(type(patamar_str)))

    if 'ANO   DURACAO MENSAL DOS PATAMARES DE CARGA' not in patamar_str:
        raise Exception("Input string does not seem to represent a patamar.dat "
                        "string. Check the input")
    

    begin = 'ANO   DURACAO MENSAL DOS PATAMARES DE CARGA'
    end = ' SUBSISTEMA'

    duracao_patamares = utils_files.select_document_part(patamar_str, begin, end)

    # eliminando as linhas antes e depois dos dados     
    duracao_patamares_str = '\n'.join(duracao_patamares.splitlines()[3:])

    return duracao_patamares_str

def get_duracao_patamares_dict(duracao_patamares_str: str) -> dict:
    '''
    Retorna um objeto contendo as duracoes de patamar, distribuidos em ano, mes
     e tipo de patamar, interpretados a partir do bloco de duracoes de patamar
     do arquivo patamar.dat

     : duracao_patamares_str deve ser a string obtida atraves da funcao
      'get_duracao_patamares_str()'
    '''
    
    if type(duracao_patamares_str) != str:
        raise Exception("'get_duracao_patamares_dict' can only receive a string."
                        "{} is not a valid input type".format(type(duracao_patamares_str)))
    # Check se o bloco possui as linhas correspondentes ao horizonte total
    if len(duracao_patamares_str.splitlines()) != 15:
        raise Exception("duracao_patamares_str possui mais de 15 linhas. Verifique")
    
    # Definindo nomes para os patamares
    switch_patamar = {0: 'pesado',1: 'medio',2: 'leve'}

    D = {}
    for i,row in enumerate(duracao_patamares_str.splitlines()):
        values = row[5:].split()
        patamar = switch_patamar.get(i%3)
        
        # Inicializando o dicionario de cada um dos anos
        if row[:5].strip() != '':
            ano = int(row[:5].strip())

            # O dicionario incorpora um dict comprehension para permitir a iteracao
            #  por cada um dos meses, e posteriormente permitir o update de cada
            #  valor de patamar.
            D.update({ano:{utils_datetime.get_br_abreviated_month(mes): {} for mes in range(1,13)}})

        # Iterando pelos meses e atualizando o dicionario final
        for mes in range(1,13):
            mes_abr = utils_datetime.get_br_abreviated_month(mes)
            D[ano][mes_abr].update({patamar: float(values[mes-1])})
    
    return D


def get_duracao_patamares_df(duracao_patamares_dict: dict) -> pd.DataFrame:
    '''
    Retorna um DataFrame a partir do dicionario interpretado da duracao de patamares
     : duracao_patamares_dict deve ser o dict obtida atraves da funcao
      'get_duracao_patamares_dict()'
    '''
    
    if type(duracao_patamares_dict) != dict:
        raise Exception("'get_duracao_patamares_df' can only receive a dictionary."
                        "{} is not a valid input type".format(type(duracao_patamares_dict)))
    
    # Iterando pelas chaves do dicionario e construindo linhas de um dataframe
    L = []
    for ano, valores_ano in duracao_patamares_dict.items():
        for mes, valores_mes  in valores_ano.items():
            row = {
                'ano': ano,
                'mes': utils_datetime.get_br_abreviated_month_number(mes),
                'pesado': valores_mes['pesado'],
                'medio': valores_mes['medio'],
                'leve': valores_mes['leve'],
            }
            L.append(row)

    return pd.DataFrame(L).set_index(['ano', 'mes'])

# =================================== CARGA ====================================
def get_carga_str(patamar_str: str) -> str:
    """
    Retorna a substring correspondente ao bloco de carga de um 
     arquivo patamar.dat em seu formato string.
    """
    if type(patamar_str) != str:
        raise Exception("'get_carga_str' can only receive a string."
                        "{} is not a valid input type".format(type(patamar_str)))

    if 'ANO   DURACAO MENSAL DOS PATAMARES DE CARGA' not in patamar_str:
        raise Exception("Input string does not seem to represent a patamar.dat "
                        "string. Check the input")
    

    begin = ' SUBSISTEMA'
    end = ' SUBSISTEMA'

    carga = utils_files.select_document_part(patamar_str, begin, end)

    # eliminando as linhas antes e depois dos dados     
    carga_str = '\n'.join(carga.splitlines()[4:-1])

    return carga_str

def get_carga_dict(carga_str: str) -> dict:
    '''
    Retorna um objeto contendo os P.Us de patamares de caraga, distribuidos
     em ano, mes e tipo de patamar, interpretados a partir do bloco de carga
     do arquivo patamar.dat

     : carga_str deve ser a string obtida atraves da funcao
      'get_carga_str()'
    '''
    
    if type(carga_str) != str:
        raise Exception("'get_carga_dict' can only receive a string."
                        "{} is not a valid input type".format(type(carga_str)))
    # Check se o bloco possui as linhas correspondentes ao horizonte total
    if len(carga_str.splitlines()) != 64:
        raise Exception("carga_str nao parece representar o bloco de carga do arquivo patamar.dat. Verifique")
    
    # Definindo nomes para os patamares
    switch_patamar = {0: 'pesado', 1: 'medio', 2: 'leve'}

    idx = 0
    D = {}
    for i, row in enumerate(carga_str.splitlines()):
        patamar = switch_patamar.get(idx%3)

        # Inicializando o dicionário dos submercados:
        if i%16 == 0:
            submercado = int(row.strip())
            D.update({submercado: {}})
            continue


        # Atualizando o dicionario de submercados para cada um dos anos
        if row[:7].strip() != '':
            ano = int(row[:7].strip())

            # O dicionario incorpora um dict comprehension para permitir a iteracao
            #  por cada um dos meses, e posteriormente permitir o update de cada
            #  valor de patamar.
            D[submercado].update({ano:{utils_datetime.get_br_abreviated_month(mes): {} for mes in range(1,13)}})


        values = [float(value) for value in row[7:].split()]
        # Iterando pelos meses e atualizando o dicionario final
        for mes in range(1,13):
            mes_abr = utils_datetime.get_br_abreviated_month(mes)
            D[submercado][ano][mes_abr].update({patamar: float(values[mes-1])})

        idx += 1
    
    return D

def get_carga_df(carga_dict: dict) -> pd.DataFrame:
    '''
    Retorna um DataFrame a partir do dicionario interpretado dos P.Us de carga
     : carga_dict deve ser o dict obtida atraves da funcao
      'get_carga_dict()'
    '''
    
    if type(carga_dict) != dict:
        raise Exception("'get_carga_df' can only receive a dictionary."
                        "{} is not a valid input type".format(type(carga_dict)))
    
    # Iterando pelas chaves do dicionario e construindo linhas de um dataframe
    L = []
    for submercado, dict_submercado in carga_dict.items():
        for ano, dict_ano in dict_submercado.items():
            for mes, valores_mes in dict_ano.items():
                row = {
                    'submercado': submercado,
                    'ano': ano, 
                    'mes': utils_datetime.get_br_abreviated_month_number(mes),
                    'pesado': valores_mes['pesado'],
                    'medio': valores_mes['medio'],
                    'leve': valores_mes['leve'],
                }
                L.append(row)

    return pd.DataFrame(L)

# =============================== INTERCAMBIO ==================================
def get_intercambio_str(patamar_str: str) -> str:
    """
    Retorna a substring correspondente ao bloco de intercambios de um 
     arquivo patamar.dat em seu formato string.
    """
    if type(patamar_str) != str:
        raise Exception("'get_intercambio_str' can only receive a string."
                        "{} is not a valid input type".format(type(patamar_str)))

    if 'INTERCAMBIO(P.U.INTERC.MEDIO)' not in patamar_str:
        raise Exception("Input string does not seem to represent a patamar.dat "
                        "string. Check the input")
    

    begin = '   A ->B'
    end = ' SBM  BLOCO'

    intercambio = utils_files.select_document_part(patamar_str, begin, end)

    # eliminando as linhas antes e depois dos dados     
    intercambio_str = '\n'.join(intercambio.splitlines()[4:-1])

    return intercambio_str

def get_intercambio_dict(intercambio_str: str) -> dict:
    '''
    Retorna um objeto contendo os P.Us de intercambio, distribuidos em ano,
     mes e tipo de patamar, interpretados a partir do bloco de intercambios
     do arquivo patamar.dat

     : intercambio_str deve ser a string obtida atraves da funcao
      'get_intercambio_str()'
    '''
    
    if type(intercambio_str) != str:
        raise Exception("'get_intercambio_dict' can only receive a string."
                        "{} is not a valid input type".format(type(intercambio_str)))
    # Check se o bloco possui as linhas correspondentes ao horizonte total
    if len(intercambio_str.splitlines()) != 192:
        raise Exception("intercambio_str nao parece representar o bloco de intercambio do arquivo patamar.dat. Verifique")
    
    # Definindo nomes para os patamares
    switch_patamar = {0: 'pesado', 1: 'medio', 2: 'leve'}

    idx = 0
    D = {}
    for i, row in enumerate(intercambio_str.splitlines()):
        patamar = switch_patamar.get(idx%3)

        # Inicializando o dicionário dos intercambios:
        if i%16 == 0:
            intercambio = '->'.join(row.strip().split())
            D.update({intercambio: {}})
            continue

        # Atualizando o dicionario de intercambios para cada um dos anos
        if row[:7].strip() != '':
            ano = int(row[:7].strip())

            # O dicionario incorpora um dict comprehension para permitir a iteracao
            #  por cada um dos meses, e posteriormente permitir o update de cada
            #  valor de patamar.
            D[intercambio].update({ano:{utils_datetime.get_br_abreviated_month(mes): {} for mes in range(1,13)}})


        values = [float(value) for value in row[7:].split()]
        # Iterando pelos meses e atualizando o dicionario final
        for mes in range(1,13):
            mes_abr = utils_datetime.get_br_abreviated_month(mes)
            D[intercambio][ano][mes_abr].update({patamar: float(values[mes-1])})

        idx += 1
    
    return D

def get_intercambio_df(intercambio_dict: dict) -> pd.DataFrame:
    '''
    Retorna um DataFrame a partir do dicionario interpretado dos P.Us de intercambio
     : intercambio_dict deve ser o dict obtida atraves da funcao
     'get_intercambio_dict()'
    '''
    
    if type(intercambio_dict) != dict:
        raise Exception("'get_intercambio_df' can only receive a dictionary."
                        "{} is not a valid input type".format(type(intercambio_dict)))
    
    # Iterando pelas chaves do dicionario e construindo linhas de um dataframe
    L = []
    for intercambio, intercambios_obj in intercambio_dict.items():
        for ano, anos_obj in intercambios_obj.items():
            for mes, patamares_obj in anos_obj.items():
                row = {
                    'intercambio': intercambio,
                    'ano': ano, 
                    'mes': utils_datetime.get_br_abreviated_month_number(mes),
                    'pesado': patamares_obj['pesado'],
                    'medio': patamares_obj['medio'],
                    'leve': patamares_obj['leve'],
                }
                L.append(row)

    return pd.DataFrame(L)

# =============================== NAO SIMULADAS ================================
def get_nao_simuladas_str(patamar_str: str) -> str:
    """
    Retorna a substring correspondente ao bloco de usinas nao simuladas 
     de um arquivo patamar.dat em seu formato string.
    """
    if type(patamar_str) != str:
        raise Exception("'get_nao_simuladas_str' can only receive a string."
                        "{} is not a valid input type".format(type(patamar_str)))

    if 'BLOCO DE USINAS NAO SIMULADAS' not in patamar_str:
        raise Exception("Input string does not seem to represent a patamar.dat "
                        "string. Check the input")
        
    begin = ' SBM  BLOCO'
    begin_idx = patamar_str.find(begin)
    
    # eliminando as linhas antes e depois dos dados     
    nao_simuladas_str = '\n'.join(patamar_str[begin_idx:].splitlines()[4:])

    return nao_simuladas_str

def get_nao_simuladas_dict(nao_simuladas_str: str) -> dict:
    '''
    Retorna um objeto contendo os P.Us de usinas nao simuladas, distribuidos em submercado
     ano, mes e tipo de patamar, interpretados a partir do bloco de nao simuladas
     do arquivo patamar.dat

     : usinas_nao_simuladas_str deve ser a string obtida atraves da funcao
      'get_nao_simuladas_str()'
    '''
    
    if type(nao_simuladas_str) != str:
        raise Exception("'get_usinas_nao_simuladas_dict' can only receive a string."
                        "{} is not a valid input type".format(type(nao_simuladas_str)))
    # Check se o bloco possui as linhas correspondentes ao horizonte total
    if len(nao_simuladas_str.splitlines()) != 256:
        raise Exception("usinas_nao_simuladas_str nao parece representar o bloco de nao simuladas do arquivo patamar.dat. Verifique")
    
    # Definindo nomes para os patamares
    switch_patamar = {0: 'pesado', 1: 'medio', 2: 'leve'}
    switch_submercado = {1: "SE", 2: "S", 3: "NE", 4: "N"}
    switch_tipo = {1: "PCH", 2: "PCT", 3: "EOL", 4: "UFV"}

    idx = 0
    
    # Inicializando objeto
    D = {
        'SE': {"PCH": {}, "PCT": {}, "EOL": {}, "UFV": {}},
        'S': {"PCH": {}, "PCT": {}, "EOL": {}, "UFV": {}},
        'NE': {"PCH": {}, "PCT": {}, "EOL": {}, "UFV": {}},
        'N': {"PCH": {}, "PCT": {}, "EOL": {}, "UFV": {}}
    }
    for i, row in enumerate(nao_simuladas_str.splitlines()):
        patamar = switch_patamar.get(idx%3)

        # Capturando as referencias do bloco:
        if i%16 == 0:
            submercado = switch_submercado.get(int(row.strip().split()[0]))
            tipo_usina = switch_tipo.get(int(row.strip().split()[1]))
            continue

        # Atualizando o dicionario de intercambios para cada um dos anos
        if row[:7].strip() != '':
            ano = int(row[:7].strip())

            # O dicionario incorpora um dict comprehension para permitir a iteracao
            #  por cada um dos meses, e posteriormente permitir o update de cada
            #  valor de patamar.

            D[submercado][tipo_usina].update({ano:{utils_datetime.get_br_abreviated_month(mes): {} for mes in range(1,13)}})


        values = [float(value) for value in row[7:].split()]
    #     # Iterando pelos meses e atualizando o dicionario final
        for mes in range(1,13):
            mes_abr = utils_datetime.get_br_abreviated_month(mes)
            D[submercado][tipo_usina][ano][mes_abr].update({patamar: float(values[mes-1])})

        idx += 1
    
    return D

def get_nao_simuladas_df(nao_simuladas_dict: dict) -> pd.DataFrame:
    '''
    Retorna um DataFrame a partir do dicionario interpretado dos P.Us de usinas nao simuladas
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
                for mes, patamares_obj in anos_obj.items():
                    row = {
                        'submercado': submercado,
                        'tipo': usina,
                        'ano': int(ano), 
                        'mes': utils_datetime.get_br_abreviated_month_number(mes),
                        'pesado': patamares_obj['pesado'],
                        'medio': patamares_obj['medio'],
                        'leve': patamares_obj['leve'],
                    }
                    L.append(row)

    return pd.DataFrame(L)