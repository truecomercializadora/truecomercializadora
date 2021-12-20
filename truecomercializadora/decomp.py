import calendar
import datetime
import os
import zipfile

from . import utils_datetime
from . import utils_files

from . import ccee
from . import ons
import boto3

def get_estagios(ano: int, mes: int) -> list:
    """
    Retorna uma lista de dicionarios contendo as informacoes de cada estagio do modelo a
      partir do ano e mes do estudo de interesse
    """
    if mes + 1 == 13:
        semanas_operativas = ons.get_semanas_operativas(ano, mes) + ons.get_semanas_operativas(ano + 1,1)
    else:
        semanas_operativas = ons.get_semanas_operativas(ano, mes) + ons.get_semanas_operativas(ano, mes + 1)

    estagios = []
    semanas_mes_seguinte = []
    ultimo_estagio = {}
    for semana in semanas_operativas:
        data_inicio = semana['inicio']
        data_fim = semana['fim']
        intervalo_semana = [dia.month for dia in utils_datetime.get_list_of_dates_between_days(data_inicio, data_fim)]
        if mes in intervalo_semana:
            estagios.append(semana)
        if (mes not in intervalo_semana) and ( ((mes % 12) + 1) in intervalo_semana):
            semanas_mes_seguinte.append(semana)
    
    if semanas_mes_seguinte[-1]['fim'].month == 12:
        ultimo_dia = datetime.date(semanas_mes_seguinte[-1]['fim'].year + 1, 1, 1) - datetime.timedelta(days = 1)
    else:
        ultimo_dia = datetime.date(semanas_mes_seguinte[-1]['fim'].year, (semanas_mes_seguinte[-1]['fim'].month % 12) + 1, 1) - datetime.timedelta(days = 1)

    ultimo_estagio['inicio'] = semanas_mes_seguinte[0]['inicio']
    ultimo_estagio['fim'] = ultimo_dia
    ultimo_estagio['semana_inicio'] = semanas_mes_seguinte[0]['semana']
    ultimo_estagio['semana_fim'] = semanas_mes_seguinte[-1]['semana']
    ultimo_estagio['rev_inicio'] = semanas_mes_seguinte[0]['rev']
    ultimo_estagio['rev_fim'] = semanas_mes_seguinte[-1]['rev']

    estagios.append(ultimo_estagio)
    return estagios


def get_dias_do_mes_por_estagio(estagios_decomp):
    """
    Retorna uma lista de inteiros representando o numero de dias de cada estagio que pertem-
      cem ao mes do deck
    """

    # Obtendo o mes e ano do decomp atraves do segundo estagio    
    mes = estagios_decomp[1]['fim'].month
    ano = estagios_decomp[1]['fim'].year
    
    dias = [
        utils_datetime.count_days_in_month(
            utils_datetime.get_list_of_dates_between_days(estagio['inicio'], estagio['fim']),
            mes
        ) for estagio in estagios_decomp
    ]

    # Garantindo que o total de dias do mes nos estagios e o mesmo que o total de dias do mes do deck     
    if sum(dias) != calendar.monthrange(ano, mes)[1]:
        raise Exception("get_dias_do_mes_por_estagio returned a total of {} days where {}-{} has only {} days".format(sum(dias), ano, mes, calendar.monthrange(ano, mes)[1]))

    return dias

def get_horas_por_patamar(
    estagio_decomp: dict ,
    patamares_horarios: dict,
    mes: int=None) -> dict:
    """
    Retorna um dicionario de horas por patamar de carga para um determinado estagio do DECOMP
      o input 'semana_operativa'  deve ser o mesmo dicionario retornado na lista da funcao
      'get_estagios'.
    """
    
    ano_patamares = int(list(patamares_horarios['jan'].keys())[-1].split('-')[0])
    inicio_semana = estagio_decomp['inicio']
    fim_semana = estagio_decomp['fim']
    if mes:
        dias_semana = [d for d in utils_datetime.get_list_of_dates_between_days(inicio_semana, fim_semana) if d.month == mes]
    else:
        dias_semana =  utils_datetime.get_list_of_dates_between_days(inicio_semana, fim_semana)

    # Inicializando o dicionario com as horas de cada patamar
    horas_patamar = {
        'pesada': 0,
        'media': 0,
        'leve': 0,
    }
    for dia in dias_semana:
        # Ajuste para considerar os patamares do ano anterior em um caso de patamar de longo prazo.
        dia_str = dia.strftime('%Y-%m-%d')
        if dia.year > ano_patamares:
            dia = datetime.date(ano_patamares, dia.month, dia.day)
            dia_str = dia.strftime('%Y-%m-%d')
        elif dia.year < ano_patamares:
            dia = datetime.date(dia.year, 1, dia.day)

        mes = utils_datetime.get_br_abreviated_month(dia.month)
        patamares = patamares_horarios[mes][dia_str]
        horas_patamar['pesada'] = horas_patamar['pesada'] + len([horario['hora'] for horario in patamares if horario['patamar'] == "pesado"])
        horas_patamar['media'] = horas_patamar['media'] + len([horario['hora'] for horario in patamares if horario['patamar'] == "medio"])
        horas_patamar['leve'] = horas_patamar['leve'] + len([horario['hora'] for horario in patamares if horario['patamar'] == "leve"])
        
    return horas_patamar

def get_prevs_file_paths(decomp_zip):
    """
    Returna um dicionario de caminhos para os prevs referentes ao Zip do Deck DECOMP fornecido.
    A funcao deve receber uma classe zipfile.ZipFile que pode ser construida, por exemplo,
      atraves da funcao 'build_zipfile_from_bytesarray' disponivel em 'utils_files'.
    """
    if type(decomp_zip) != zipfile.ZipFile:
        raise Exception("'get_prevs_file_paths' can only receive a zipfile.Zipfile class")
    
    return {
        os.path.split(file)[0]: file for file in decomp_zip.namelist() if 'prevs.rv' in file and file[-2] == 'v'
    }

def get_sensibilizacoes(decomp_zip):
    """
    Returna uma lista de nomes das sensibilizacoes realizadas no estudo realizado pelo deck.
      As sensibilizacoes sao identificadas atraves dos arquivos Prevs.rv# contidos no deck.
      A funcao deve receber uma classe zipfile.ZipFile que pode ser construida, por exemplo,
      atraves da funcao 'build_zipfile_from_bytesarray' disponivel em 'utils_files'.
    """
    if type(decomp_zip) != zipfile.ZipFile:
        raise Exception("'get_prevs_file_paths' can only receive a zipfile.Zipfile class")
    
    return sorted([os.path.split(prevs)[0] for prevs in list(get_prevs_file_paths(decomp_zip).values()) ])


def get_relato_file_paths(decomp_zip):
    """
    Returna um dicionario de caminhos para os arquivos 'relato.rv#' referentes ao Zip do Deck
      DECOMP fornecido. A funcao deve receber uma classe zipfile.ZipFile. A classe pode ser
      construida, por exemplo, atraves da funcao disponivel em: 
              'utils_files.build_zipfile_from_bytesarray' 
    Se nenhum arquivo 'relato.rv#' for encontrado no zipfile, a funcao retorna None
    """
    if type(decomp_zip) != zipfile.ZipFile:
        raise Exception("'get_relato_file_paths' can only receive a zipfile.Zipfile class.")
    
    D = {os.path.split(file)[0]:file for file in decomp_zip.namelist() if 'relato.rv' in file and len(file.split('.')) == 2}
    return D


def get_sumario_file_paths(decomp_zip):
    """
    Returna um dicionario de caminhos para os arquivos 'sumario.rv#' referentes ao Zip do Deck
      DECOMP fornecido. A funcao deve receber uma classe zipfile.ZipFile. A classe pode ser 
      construida, por exemplo, atraves da funcao disponivel em:
              'utils_files.build_zipfile_from_bytesarray'
    Se nenhum arquivo 'sumario.rv#' for encontrado no zipfile, a funcao retorna None
    """
    if type(decomp_zip) != zipfile.ZipFile:
        raise Exception("'get_sumario_file_paths' can only receive a zipfile.Zipfile class.")
    
    D = {os.path.split(file)[0]:file for file in decomp_zip.namelist() if 'sumario.rv' in file and len(file.split('.')) == 2}
    return D


def get_cmo_relato(relato_str):
    """
    Retorna um dicionario contendo os custos marginais de operacao do primeiro estagio
      a partir do relato.rv# de uma sensibilidade do DECOMP.
    """
    begin = utils_files.find_all_occurences_of_substring(relato_str, 'Custo marginal de operacao do subsistema')[0]

    lines = relato_str[begin:].splitlines()[:7]
    cmo_lines = lines[:5]
    cmo = {
        custo.replace('Custo marginal de operacao do subsistema ', '').replace(' ($/MWh)','').replace(':','').strip().split()[0]: float(custo.replace('Custo marginal de operacao do subsistema ', '').replace(' ($/MWh)','').replace(':','').strip().split()[1])
        for custo in cmo_lines
    }
    
    inviavel = False
    inviabilidades = ''
    if 'OPERACAO INVIAVEL' in lines[6]:
        inviavel = True
        inviabilidades = lines[5:]
    return {
        **cmo,
        'inviavel': inviavel,
        'inviabilidades': ''.join(inviabilidades).strip()
    }

def get_pld_sumario(sumario_str,ano_deck):
    """
    Retorna um dicionario contendo os custos marginais de operacao considerando os valores
      maximos e minimos de Preco de Liquidacao de Diferencas, definidos pela CCEE.
    Os custos são inferidos a partir do sumario.rv# transcrito para uma string.
    """
    if type(sumario_str) != str:
        raise Exception("'get_pld_sumario' can only receive a sumario.rv# string.")
        
    if 'CUSTO MARGINAL DE OPERACAO' not in sumario_str:
        raise Exception("'get_pld_sumario' input str does not seem to represent a sumario.rv# file. Verify the input content.")
    
    begin = 'CUSTO MARGINAL DE OPERACAO'
    end = 'Patamares de carga: 1 - Pesada, 2 - Media, 3 - Leve'
    cmo_report = utils_files.select_document_part(sumario_str, begin, end)
    cmo_lines = cmo_report.splitlines()[4:-2]
    
    subsistemas = ['SE','S', 'NE', 'N', 'FC']
    patamares = ['pesada', 'media', 'leve', 'medio']
    D = {'SE': {}, 'S': {}, 'NE':{}, 'N': {}, 'FC': {}}
    
    idx_substistema = 0
    piso, teto = ccee.get_pld_db(ano_deck=ano_deck)
    print(piso, teto)
    for i,line in enumerate(cmo_lines):
        subsistema = subsistemas[idx_substistema] 
        patamar = patamares[i%4]
        valores = [ccee.adjust_teto_piso(float(value),piso, teto) for value in line.split()[1:]]
        if i%4 == 3:
            idx_substistema += 1
        D[subsistema].update({
            patamar: valores
        })
    return D

def get_pld_medio_semanal_from_sumario(sumario_str, rev, estagios_decomp, patamares_horarios,ano_deck):
    """
    Retorna um dicionario contendo os plds medios semanais de cada um dos submercados. A
      partir da str representando o sumario.rv# e ja considerando os valores de pld max e min
    A funcao depende tambem do objeto construido atraves da funcao do modulo ccee capaz de
      construir os patamares horarios do ano desejado. 'get_patamares_horarios'
    """

    if type(sumario_str) != str:
        raise Exception("'get_pld_medio_semanal_from_sumario' can only receive a sumario.rv# string.")
        
    if 'CUSTO MARGINAL DE OPERACAO' not in sumario_str:
        raise Exception("'get_pld_medio_semanal_from_sumario' input str does not seem to represent a sumario.rv# file. Verify the input content.")

    if type(estagios_decomp) != list:
        raise Exception("'get_pld_medio_semanal_from_sumario' should receive a list of 'estagios_decomp'. 'estagios_decomp' of type {} detected.".format(type(estagios_decomp)))
    
    if type(patamares_horarios) != dict:
        raise Exception("'get_pld_medio_semanal_from_sumario' should receive a dict of 'patamares_horarios'. 'patamares_horarios' of type {} detected.".format(type(patamares_horarios)))

    plds = get_pld_sumario(sumario_str,ano_deck)
    D = {"SE": [], 'S': [], 'NE': [], "N": []}
    for i,estagio in enumerate(estagios_decomp[rev:-1]):

        # pld_sudeste = plds['SE']['medio'][i]
        # pld_sul = plds['S']['medio'][i]
        # pld_nordeste = plds['NE']['medio'][i]
        # pld_norte = plds['N']['medio'][i]        

        h_patamar = get_horas_por_patamar(estagio, patamares_horarios)
        pld_sudeste = (plds['SE']['pesada'][i]*h_patamar['pesada'] + plds['SE']['media'][i]*h_patamar['media'] + plds['SE']['leve'][i]*h_patamar['leve'])/sum(h_patamar.values())
        pld_sul = (plds['S']['pesada'][i]*h_patamar['pesada'] + plds['S']['media'][i]*h_patamar['media'] + plds['S']['leve'][i]*h_patamar['leve'])/sum(h_patamar.values())
        pld_nordeste = (plds['NE']['pesada'][i]*h_patamar['pesada'] + plds['NE']['media'][i]*h_patamar['media'] + plds['NE']['leve'][i]*h_patamar['leve'])/sum(h_patamar.values())
        pld_norte = (plds['N']['pesada'][i]*h_patamar['pesada'] + plds['N']['media'][i]*h_patamar['media'] + plds['N']['leve'][i]*h_patamar['leve'])/sum(h_patamar.values())

        D['SE'].append(pld_sudeste)
        D['S'].append(pld_sul)
        D['NE'].append(pld_nordeste)
        D['N'].append(pld_norte)
    return D

def get_pld_mensal(pld_semanal, estagios):
    """
    Retorna um dicionario contendo os plds medios mensais de cada um dos submercados. As me-
     sao calculadas a partir do dicionario obtido por 'get_pld_medio_semanal_from_sumario'
     disponivel neste mesmo modulo. Alem disso a funcao tambem utiliza a lista de estagios do
     decomp obtido atraves de 'get_estagios'
    """
    
    if type(pld_semanal) != dict:
        raise Exception("'get_pld_medio_semanal_from_sumario' should receive a dict of 'pld_semanal'. 'pld_semanal' of type {} detected.".format(type(pld_semanal)))
    
    if type(estagios) != list:
        raise Exception("'get_pld_medio_semanal_from_sumario' should receive a list of 'estagios_decomp'. 'estagios_decomp' of type {} detected.".format(type(estagios)))

    
    dias_estagios = get_dias_do_mes_por_estagio(estagios)    
    return {
        'pldMensalSE': round(sum([pld*dias_estagios[i] for i,pld in enumerate(pld_semanal['SE'])])/sum(dias_estagios),2),
        'pldMensalS': round(sum([pld*dias_estagios[i] for i,pld in enumerate(pld_semanal['S'])])/sum(dias_estagios),2),
        'pldMensalNE': round(sum([pld*dias_estagios[i] for i,pld in enumerate(pld_semanal['NE'])])/sum(dias_estagios),2),
        'pldMensalN': round(sum([pld*dias_estagios[i] for i,pld in enumerate(pld_semanal['N'])])/sum(dias_estagios),2)
    }

def get_relatorios_balanco_energetico(relato_str):
    """
    Retorna um dicionario contendo os dados do cabecalho de um rela-
    torio de de balanco energetico.
    """
    
    if type(relato_str) != str:
        raise Exception("'get_relatorios_balanco_energetico' can only receive a string. {} is not a valid input.".format(relato_str))
        
    if 'RELATORIO  DO  BALANCO  ENERGETICO' not in relato_str:
        raise Exception("Input string does not seem to represent a relato.rv# string. Check the input")
    
    begin = 'RELATORIO  DO  BALANCO  ENERGETICO'
    end = 'RELATORIO  DA  OPERACAO'
    return utils_files.select_document_parts(relato_str, begin, end)

def get_heading_balanco_energetico(relatorio_subsistema_str):
    """
    Retorna um dicionario contendo os dados do cabecalho de um rela-
    torio de de balanco energetico.
    """
    re_patterns = {'EAR_ini:':'','ENA:':'', 'EAR_fim:':'', '(%EARM)':'', '(MWmes)':'','(Mwmes)':'','(MWmed)':''}
    linhas = [line.strip().split() for line in utils_files.replace_ocurrences_in_string(re_patterns, relatorio_subsistema_str).splitlines()[1:3]]
    dados = list(zip(linhas[0], linhas[1]))
    return {
        'ear_ini': {'mw_mes': float(dados[0][0]), 'percent_ear': round(float(dados[0][1])/100,3)},
        'ena': {'mw_med': float(dados[1][0]), 'percent_ear': round(float(dados[1][1])/100,3)},
        'ear_fim': {'mw_mes': float(dados[2][0]), 'percent_ear': round(float(dados[2][1])/100,3)}
    }

def get_resumo_de_balancos_energeticos(relato_str):
    """
    Retorna uma lista de dicionarios. Cada item da lista representa o resumo
    do balanco energetico de uma semana sob o ponto de vista dos subsistemas.
    As energias (EAR e ENA) estao representadas dentro do dicionario do sub-
    sistema:
        [
            {
                "SE": {
                'ear_ini':{'mw_mes': float, 'percent_ear': float},
                'ena': {'mw_med': float, 'percent_ear': float},
                'ear_fim': {'mw_mes': float, 'percent_ear': float}
                },
                ...
            },
            ...
        ]
    """

    if type(relato_str) != str:
        raise Exception("'get_resumo_de_balancos_energeticos' can only receive a string. {} is not a valid input.".format(relato_str))
        
    if 'RELATORIO  DO  BALANCO  ENERGETICO' not in relato_str:
        raise Exception("Input string does not seem to represent a relato.rv# string. Check the input")
    
    relatorios = get_relatorios_balanco_energetico(relato_str)
    
    begin_SudesteSul = 'Subsistema S'
    begin_NordesteNorte = 'Subsistema N'
    end='total da energia importada'

    L = []
    for relatorio in relatorios:
        relatorio_sudeste_sul = utils_files.select_document_parts(relatorio, begin_SudesteSul, end)
        relatorios_nordeste_norte = utils_files.select_document_parts(relatorio, begin_NordesteNorte, end)

        L.append({
            'SE': get_heading_balanco_energetico(relatorio_sudeste_sul[0]),
            'S': get_heading_balanco_energetico(relatorio_sudeste_sul[1]),
            'NE': get_heading_balanco_energetico(relatorios_nordeste_norte[0]),
            'N': get_heading_balanco_energetico(relatorios_nordeste_norte[1])
        })
    return L

def get_enas_pre_estudo_subsitema(relato_str):
    """
    Retorna um dicionario contendo as ENAs pre estudo de cada subsistema a
     partir do relato.rv# de uma sensibilidade do DECOMP.
    """
    if type(relato_str) != str:
        raise Exception("'get_resumo_de_balancos_energeticos' can only receive a string. {} is not a valid input.".format(relato_str))

    if 'RELATORIO DOS DADOS DE ENERGIA NATURAL AFLUENTE POR SUBSISTEMA' not in relato_str:
        raise Exception("Input string does not seem to represent a relato.rv# string. Check the input")

    begin = 'RELATORIO DOS DADOS DE ENERGIA NATURAL AFLUENTE POR SUBSISTEMA'
    end = ' *Referencia: fim do estudo'
    relatorio_ena = utils_files.select_document_part(relato_str, begin, end)

    return {
        submercado.split()[0]: list(map(lambda x: float(x),submercado.split()[3:]))
            for submercado in relatorio_ena.splitlines()[5:-3]
    }

