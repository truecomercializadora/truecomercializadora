'''
 Modulo para funcoes especificas de calculos envolvendo o arquivo prevs.
'''


from . import decomp
from . import utils_datetime

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
    if hidrograma_type not in ['A', 'B', 'medio']:
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

def _calculate_vazao_artificial(id_posto: int, prevs: dict, postos_vazao: dict) -> list:
    '''
    Calcula a lista de vazoes artificiais (1 para cada semana do prevs) de um determinado posto.
     A funcao deve receber o id do posto, o dicionario contendo as listas de vazoes de cada posto
     do prevs.rv#, e um dicionario contendo todos os postos, artificiais ou nao.
    '''
    if type(id_posto) != int:
        raise Exception("'calculate_vazao_vazao_artificial' can only receive an integer for id_posto."
                        "{} is not a valid input type".format(type(id_posto)))
    if type(prevs) != dict:
        raise Exception("'calculate_vazao_vazao_artificial' can only receive a dictionary for prevs_obj."
                        "{} is not a valid input type".format(type(prevs)))
        
    vazoes = []
    for i in range(6):
        if id_posto == 37:
            vazoes.append(prevs[237][i] - 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) - prevs[117][i] - prevs[118][i])
        if id_posto == 38:
            vazoes.append(prevs[238][i] - 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) - prevs[117][i] - prevs[118][i])
        if id_posto == 39:
            vazoes.append(prevs[239][i] - 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) - prevs[117][i] - prevs[118][i])
        if id_posto == 40:
            vazoes.append(prevs[240][i] - 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) - prevs[117][i] - prevs[118][i])
        if id_posto == 42:
            vazoes.append(prevs[242][i] - 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) - prevs[117][i] - prevs[118][i])
        if id_posto == 43:
            vazoes.append(prevs[243][i] - 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) - prevs[117][i] - prevs[118][i])
        if id_posto == 44:
            vazoes.append(prevs[244][i] - 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) - prevs[117][i] - prevs[118][i])
        if id_posto == 45:
            vazoes.append(prevs[245][i] - 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) - prevs[117][i] - prevs[118][i])
        if id_posto == 46:
            vazoes.append(prevs[246][i] - 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) - prevs[117][i] - prevs[118][i])
        if id_posto == 66:
            vazoes.append(prevs[266][i] - 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) - prevs[117][i] - prevs[118][i])
        if id_posto == 70:
            vaz_reduzida_auxiliar = prevs[73][i] - 10
            vazoes.append(prevs[73][i] - min([vaz_reduzida_auxiliar,173.5]))
        if id_posto == 75:
            vaz_reduzida_auxiliar = prevs[73][i] - 10
            vazoes.append(prevs[76][i] + min([vaz_reduzida_auxiliar,173.5]))
        if id_posto == 104:
            vazoes.append(prevs[117][i] + prevs[118][i])
        if id_posto == 109:
            vazoes.append(prevs[118][i])
        if id_posto == 116:
            vazao = prevs[119][i] - prevs[118][i]
            if vazao < 0: vazao = 0
            vazoes.append(vazao)
        if id_posto == 119:
            vazoes.append((prevs[118][i] - 0.185) / 0.8103)
        try:
            if id_posto == 126:
                vaz_referencia = postos_vazao[127][i]
                vaz_referencia_reduzida = vaz_referencia - 90
                if vaz_referencia <= 430 :
                    vazao_calculada = max([0, vaz_referencia_reduzida])
                    print(id_posto,i, vazao_calculada)
                    vazoes.append(vazao_calculada)
                elif vaz_referencia > 430:
                    print(id_posto,i, 340)
                    vazoes.append(340)
        except:
            pass
        try:
            if id_posto == 127:
                vazao_calculada = prevs[129][i] - postos_vazao[298][i] - prevs[203][i] + postos_vazao[304][i]
                print(id_posto,i, vazao_calculada)
                vazoes.append(vazao_calculada)
        except:
            pass
        try:
            if id_posto == 131:
                vazoes.append(min([postos_vazao[316][i], 144]))
        except:
            pass
        if id_posto == 132:
            vazoes.append(prevs[202][i] + min([prevs[201][i], 25]))
        if id_posto == 164:
            vazoes.append(prevs[161][i] - prevs[117][i] - prevs[118][i])
        if id_posto == 244:
            vazoes.append(prevs[34][i] + prevs[243][i])
        if id_posto == 298:
            vaz_referencia = prevs[125][i]
            vaz_referencia_reduzida = vaz_referencia - 90
            if vaz_referencia <= 190 : vazoes.append((vaz_referencia * 119)/190)
            elif 190 < vaz_referencia <= 209 : vazoes.append(119)
            elif 209 < vaz_referencia <= 250 :  vazoes.append(vaz_referencia_reduzida)
            elif vaz_referencia > 250: vazoes.append(160)
        try:
            if id_posto == 299:
                vazao_calculada = prevs[130][i] - postos_vazao[298][i] - prevs[203][i] + postos_vazao[304][i]
                print(id_posto,i, vazao_calculada)
                vazoes.append(vazao_calculada)
        except:
            pass
        try:
            if id_posto == 302:
                vazoes.append(prevs[288][i] - postos_vazao[292][i])
        except:
            pass
        try:
            if id_posto == 303:
                if postos_vazao[132][i] <= 17:
                    vazoes.append(postos_vazao[132][i])
            else:
                vazao_referencia = postos_vazao[316][i] - postos_vazao[131][i]
                vazao = 17 + min(vazao_referencia, 34)
                vazoes.append(vazao)
        except:
            pass
        try:
            if id_posto == 304:
                vazoes.append(postos_vazao[315][i] - postos_vazao[316][i])
        except:
            pass
        try:
            if id_posto == 306:
                vazao_calculada = postos_vazao[303][i] + postos_vazao[131][i]
                print(id_posto,i, vazao_calculada)
                vazoes.append(vazao_calculada)
        except:
            pass
        try:
            if id_posto == 315:
                vazoes.append(prevs[203][i] - prevs[201][i] + postos_vazao[317][i] + postos_vazao[298][i])
        except:
            pass
        try:
            if id_posto == 316:
                vazoes.append(min([postos_vazao[315][i], 190]))
        except:
            pass
        if id_posto == 317:
            vaz_referencia_reduzida = prevs[201][i] - 25
            vazoes.append(max([0, vaz_referencia_reduzida]))
        try:
            if id_posto == 318:
                vazoes.append(postos_vazao[116][i] + prevs[117][i] + prevs[118][i] + 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]) )
        except:
            pass
        if id_posto == 319:
            vazoes.append(prevs[117][i] + prevs[118][i] + 0.1 * (prevs[161][i] - prevs[117][i] - prevs[118][i]))

    return [int(vazao) for vazao in vazoes]

def _get_vazoes_artificiais(
    prevs_obj: dict,
    ano_prevs: int,
    mes_prevs: int,
    postos_artificiais: list,
    hidrograma_bmonte_table: list) -> dict:
    
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
    
    D = {}
    # Primeira passagem de calculo
    for posto in postos_artificiais:
        vazoes_posto = _calculate_vazao_artificial(
            id_posto=posto['idPosto'],
            prevs=prevs_obj,
            postos_vazao=D)
        # Calculo especifico das vazoes de Belo Monte        
        if posto['idPosto'] == 292:
            vazoes_posto = _get_vazoes_artificiais_bmonte(
                vazoes_prevs_bmonte=prevs_obj[288],
                hidrograma_table=hidrograma_bmonte_table,
                hidrograma_type='medio',
                ano=ano_prevs,
                mes=mes_prevs
            )
            D.update({posto['idPosto']: vazoes_posto})
            continue
        # Vazao depende de um posto ainda nao calculado 
        elif vazoes_posto == [] or posto['idPosto'] == 303:
            continue
        else:
            D.update({posto['idPosto']: vazoes_posto})
            continue
    
    # Criando uma lista com uma ordem especifica para evitar dependencia circular     
    lista_postos_dependencia_circular = [315,316,304,131,303,299,127,126,306]
    
    # Interando novamente para calcular os postos restantes:
    for id_posto in lista_postos_dependencia_circular:
        vazoes_posto = _calculate_vazao_artificial(
            id_posto=id_posto,
            prevs=prevs_obj,
            postos_vazao=D)
        D.update({id_posto:vazoes_posto})

    return D

def get_vazoes_obj_from_prevs(
    prevs_str: str,
    postos_table: list,
    hidrograma_bmonte_table: list,
    ano_prevs:int,
    mes_prevs:int) -> dict:
    
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
        hidrograma_bmonte_table=hidrograma_bmonte_table
    )
    
    # Concatenando os objetos:
    return {**prevs_obj, **postos_artf_obj}