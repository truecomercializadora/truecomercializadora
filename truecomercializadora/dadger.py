"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo dadger
"""
import io

from . import utils_files
from . import decomp

def get_registro_dp(dadger_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO DP (Bloco 6) de um dadger dado
     na forma de uma string
    """
    if type(dadger_str) != str:
        raise Exception("'get_registro_dp' can only receive a string."
                        "{} is not a valid input type".format(type(dadger_str)))

    if 'BLOCO 6 *** CARGA DOS SUBSISTEMAS ***' not in dadger_str:
        raise Exception("Input string does not seem to represent a dadger.rv# "
                        "string. Check the input")

    begin = "BLOCO 6"
    end = "BLOCO 7"
    registro_dp = utils_files.select_document_part(dadger_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    registro_dp = '\r\n'.join(registro_dp.splitlines()[2:-2])

    return registro_dp

def get_registro_ct(dadger_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO CT (Bloco 4) de um dadger dado
     na forma de uma string
    """
    if type(dadger_str) != str:
        raise Exception("'get_registro_ct' can only receive a string."
                        "{} is not a valid input type".format(type(dadger_str)))

    if 'BLOCO 4  ***  CADASTRO UTE  ***' not in dadger_str:
        raise Exception("Input string does not seem to represent a dadger.rv# "
                        "string. Check the input")

    begin = "BLOCO 4"
    end = "BLOCO 5"
    registro_ct = utils_files.select_document_part(dadger_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    registro_ct = '\r\n'.join(registro_ct.splitlines()[2:-2])

    return registro_ct

def write_registro_dp(
    ano_deck: int,
    mes_deck: int,
    cargas_mes_atual: list,
    cargas_mes_seguinte: list,
    patamares_table: dict) -> str:

    """
    Retorna o Registro DP a partir da tabela de cargas do mes atual e do mes se
    guinte, juntamente com a lista de patamares oficiais de carga.
    """

    if type(ano_deck) != int:
        raise Exception("'write_registro_dp' can only receive ano_deck as an integer."
                        "{} is not a valid input type".format(type(ano_deck)))
    if type(mes_deck) != int:
        raise Exception("'write_registro_dp' can only receive mes_deck as an integer."
                        "{} is not a valid input type".format(type(mes_deck)))
    if type(cargas_mes_atual) != list:
        raise Exception("'write_registro_dp' can only receive cargas_mes_atual as list."
                        "{} is not a valid input type".format(type(cargas_mes_atual)))
    if type(cargas_mes_seguinte) != list:
        raise Exception("'write_registro_dp' can only receive cargas_mes_seguinte as list."
                        "{} is not a valid input type".format(type(cargas_mes_seguinte)))
    if type(patamares_table) != dict:
        raise Exception("'write_registro_dp' can only receive patamares_table as dict."
                        "{} is not a valid input type".format(type(patamares_table)))

    # Obtendo os estagios do DECOMP
    estagios_decomp = decomp.get_estagios(ano=ano_deck,mes=mes_deck)

    master_io = io.BytesIO()
    master_io.write("&----------------------------------------------------------------------------------------------\r\n".encode("latin-1"))
    master_io.write("&                   PESADA              MEDIA               LEVE\r\n".encode('latin-1'))
    master_io.write("&   5     10  15   20        30        40        50        60        70\r\n".encode('latin-1'))
    master_io.write("&   ++    +   +    +--------++--------++--------++--------++--------++--------+\r\n".encode('latin-1'))
    master_io.write("&   IP    S  PAT     MWmed    Pat_1(h)   MWmed    Pat_2(h)   MWmed    Pat_3(h)\r\n".encode('latin-1'))
    master_io.write("&   ++    +   +    +--------++--------++--------++--------++--------++--------+\r\n".encode('latin-1'))
    master_io.write("&DP\r\n".encode('latin-1'))
    for i, semana in enumerate(estagios_decomp):
        horas_por_patamar = decomp.get_horas_por_patamar(semana, patamares_table)
        for j, subsistema in enumerate(cargas_mes_atual):
            indice = subsistema['indice']
            if i == (len(estagios_decomp)-1):
                patamar_alto = cargas_mes_seguinte[j]['cargas']['pesada']
                patamar_medio = cargas_mes_seguinte[j]['cargas']['media']
                patamar_baixo = cargas_mes_seguinte[j]['cargas']['leve']
            else:
                patamar_alto = subsistema['cargas']['pesada']
                patamar_medio = subsistema['cargas']['media']
                patamar_baixo = subsistema['cargas']['leve']
            master_io.write(
                "DP  {:>2d}   {:>2d}   3    {:>10.1f}{:>10.1f}{:>10.1f}{:>10.1f}{:>10.1f}{:>10.1f}\r\n".format(
                i+1,
                indice,
                patamar_alto,
                horas_por_patamar['pesada'],    
                patamar_medio,
                horas_por_patamar['media'],
                patamar_baixo,
                horas_por_patamar['leve'],
            ).encode('latin-1'))
            if (j+1) % 4 == 0:
                master_io.write("DP  {:>2d}   11   3              {:>10.1f}          {:>10.1f}          {:>10.1f}\r\n".format(
                    i+1,
                    horas_por_patamar['pesada'],
                    horas_por_patamar['media'],
                    horas_por_patamar['leve']
                ).encode('latin-1'))
                master_io.write("&\r\n".encode('latin-1'))

    # Retornando o buffer decoded e eliminando as linhas vazias
    return "\r\n".join(master_io.getvalue().decode('latin-1').strip().splitlines())