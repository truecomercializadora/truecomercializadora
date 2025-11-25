from copy import deepcopy
import pandas as pd
import json
import io
import numpy as np

from . import utils_s3,prevs

dict_bacias_acomph = {'grande': [1, 211, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18],
 'paranaiba': [22,251,24,25,206,207,28,205,23,209,31,32,33,99,247,248,261,294,241],
 'tiete': [118, 117, 161, 237, 238, 239, 240, 242, 243],
 'paranapanema': [47, 48, 53, 49, 249, 50, 51, 52, 57, 61, 62, 63],
 'parana': [34, 245, 154, 246, 266],
 'iguacu': [74, 76, 71, 72, 73, 77, 78, 222, 81],
 'uruguai': [215, 88, 89, 216, 217, 92, 93, 220, 94, 286, 102, 103],
 'jacui': [110, 111, 112, 113, 114, 98, 97, 284, 221, 224],
 'outras_sul': [115, 101],
 'paraguai': [278, 259, 281, 295],
 'paraiba_do_sul': [121,122,120,123,125,197,198,129,130,201,202,135],
 'doce': [262, 183, 134, 263, 149, 141, 148, 144],
 'outras_sudeste': [196, 283, 213],
 'sao_francisco': [155, 156, 158, 169, 172, 173, 178],
 'outras_nordeste': [190, 255, 188, 254],
 'tocantins': [270, 191, 253, 257, 273, 271, 275],
 'amazonas': [296,277,279,145,291,285,287,269,290,227,228,229,230,225,226,288],
 'araguari': [204, 280, 297]}


def build_postos_document(LAKE):
  obj = utils_s3.get_obj_from_s3(LAKE,'consume/ena/info/POSTOS - CONFIG.csv')
  df =  pd.read_csv(io.BytesIO(obj)).fillna('')
  dictionary = {}
  for row in df.itertuples():
    regressaoA0 = row[-24:-12]
    regressaoA1 = row[-12:]
    dictionary.update({
      row.idPosto: {
        "nome": row.nome,
        "bacia": row.bacia,
        "submercado": row.submercado,
        "tipo": row.tipo,
        "resEquivalente": row.resEquivalente,
        "produtibilidade": row.produtibilidade,
        "idPostoRegredido": row.idPostoRegredido,
        "idPostoJusante": row.idPostoJusante,
        "calculoVazao": {
          "semana1": row.vazSemana1,
          "semana2": row.vazSemana2,
          "tabelaRegressao": list(zip(regressaoA0, regressaoA1)),
          "mediaLongoTermo": row[-36:-24]
        }
      }
    })
  return dictionary

def get_postos_artificiais(postosDocument):
  return dict(
    filter(
      lambda elem: elem[1]['tipo'] == 'artificial', postosDocument.items()
    )
  )

def _build_bacia_df(acomph_io, sheet_name):
  return pd.read_excel(acomph_io, sheet_name=sheet_name, index_col=0, skiprows=4, skipfooter=6).fillna('')

def _get_lista_postos(acomph_io, sheet_name):
  df = pd.read_excel(acomph_io, sheet_name=sheet_name, index_col=0, skipfooter=40).fillna('')
  return [column for column in list(df.columns.values) if type(column) == int]

def _get_bacia_dict(acomph_io, bacia,postos_document):
  column_list = ['res_lido', 'res_consol','vaz_def_lido', 'vaz_def_consol', 'vaz_afl_lido', 'vaz_afl_consol', 'incremental', 'natural']
  df = _build_bacia_df(acomph_io, bacia)
  postos = _get_lista_postos(acomph_io, bacia)
  i = 0
  dictionary = {}
  for block in range(int(df.shape[1]/8)):
    posto_df = df[df.columns[i:i+8:]].set_axis(column_list, axis=1).round(2)
    posto = postos[block]
    if posto in postos_document:
      dictionary.update({posto: posto_df})
    i += 8
  return dictionary

def build_acomph_dict(acomph_io,postos_document):
  acomph = {
    'grande': _get_bacia_dict(acomph_io, 'Grande',postos_document),
    'paranaiba': _get_bacia_dict(acomph_io, 'Paranaíba',postos_document),
    'tiete': _get_bacia_dict(acomph_io, 'Tietê',postos_document),
    'paranapanema': _get_bacia_dict(acomph_io, 'Paranapanema',postos_document),
    'parana': _get_bacia_dict(acomph_io, 'Paraná',postos_document),
    'iguacu': _get_bacia_dict(acomph_io, 'Iguaçu',postos_document),
    'uruguai': _get_bacia_dict(acomph_io, 'Uruguai',postos_document),
    'jacui': _get_bacia_dict(acomph_io, 'Jacui',postos_document),
    'outras_sul': _get_bacia_dict(acomph_io, 'Outras Sul',postos_document),
    'paraguai': _get_bacia_dict(acomph_io, 'Paraguai',postos_document),
    'paraiba_do_sul': _get_bacia_dict(acomph_io, 'Paraíba do Sul',postos_document),
    'doce': _get_bacia_dict(acomph_io, 'Doce',postos_document),
    'outras_sudeste': _get_bacia_dict(acomph_io, 'Outras Sudeste',postos_document),
    'sao_francisco': _get_bacia_dict(acomph_io, 'São Francisco',postos_document),
    'outras_nordeste': _get_bacia_dict(acomph_io, 'Outras Nordeste',postos_document),
    'tocantins': _get_bacia_dict(acomph_io, 'Tocantins',postos_document),
    'amazonas': _get_bacia_dict(acomph_io, 'Amazonas',postos_document),
    'araguari': _get_bacia_dict(acomph_io, 'Araguari',postos_document)
  }
  return acomph


def _get_vazoes_acomph(acomph_dict, date):
  vazao = {}
  for posto in acomph_dict['postos']:
    try:
      leituras = list(filter(lambda x: x['data'] == date, posto['leituras']))[0]
    except:
      print(posto)
    vazao.update({
      posto['idPosto']: {
        "natural": leituras['vazao']['natural'],
        "incremental": leituras['vazao']['incremental']
      }
    })
  return vazao

def add_regras_vazoes_acomph(dict_regras,hidrograma_beloMonte):
    dict_regras[2] = {0: 'VAZ(1)'}
    dict_regras[203] = {0: 'VAZ(201) * 1.446'}
    dict_regras[119]=  {0: 'VAZ(118) / 0.800'}
    dict_regras.pop(118)
    dict_292 = {}
    for mes in range(1,13):
        dict_292.update({mes: 'SE(VAZ(288)<={valor},0,SE(VAZ(288)<=({valor}+13900),VAZ(288)-{valor},13900))'.format(valor = hidrograma_beloMonte[mes])})
    dict_regras[292] = dict_292
    dict_regras[168] = {0: 'VAZ(169)'}
    dict_regras[300] = {0: '0'}
    dict_regras.pop(169)
    dict_regras.pop(166)
    dict_regras.pop(260)
    
    return dict_regras

def _get_available_dates(acomph_dict):
  return [leitura['data'] for leitura in acomph_dict['postos'][0]['leituras']]

def get_hidrograma(LAKE):
    obj = utils_s3.get_obj_from_s3(LAKE,'consume/ena/info/POSTOS - BELO_MONTE.csv')
    df = pd.read_csv(io.BytesIO(obj))
    df.index = df.index+1
    dict_hidrograma = df[['medio']].to_dict(orient='dict')['medio']
    return dict_hidrograma


def _calculate_vazao_postos_artificiais(dict_regras,dict_deps,lista_postos,df_base,mes):
    df_artificiais = pd.DataFrame(index=df_base.index)
    for id_posto_artificial in lista_postos:
        try:
          prevs.calc_posto_artificial(id_posto_artificial,df_base,df_artificiais,dict_regras,dict_deps,mes)
        except:continue

    df_artificiais.loc['incremental'] = np.nan # postos artificiais com incrementais nulas
    return df_artificiais

def build_vazoes_completo(vazoes, postos_artificiais, data, fonte=None,LAKE='true-datalake-prod'):

  mes = int(data.split('/')[1])


  df_vazoes_totais = pd.DataFrame(vazoes).loc[['natural']]
  df_vazoes_incr = pd.DataFrame(vazoes).loc[['incremental']]


  hidrograma_beloMonte = get_hidrograma()

  arquivo_regras = prevs.get_regras_prevs(LAKE)
  arquivo_regras = arquivo_regras.replace('SMAP','VAZ')
  dict_regras = prevs.parse_regras(arquivo_regras)
  dict_regras = add_regras_vazoes_acomph(dict_regras,hidrograma_beloMonte)

  dict_deps = prevs.extrai_postos_regra(dict_regras)
  lista_postos_artificiais =  [key for key in dict_regras.keys() if 0 in dict_regras[key] or key == 292] # consideramos nas vazoes diarias apenas as propagacoes diarias. 

  df_base = pd.DataFrame(deepcopy(vazoes)) # não altera o original
  df_base.loc['natural',169] = df_vazoes_incr.loc['incremental',169]
  df_base = df_base.drop(columns=[col for col in dict_regras.keys() if col in df_base.columns and col not in [172,173,174,175,178]])

  df_artificiais = _calculate_vazao_postos_artificiais(dict_regras,dict_deps,lista_postos_artificiais,df_base,mes)
  vazoes.update(df_artificiais.to_dict())
  return vazoes

def build_vazoes_dict(acomph_document, postos_artificiais):
  datas_disponiveis = _get_available_dates(acomph_document)

  dictionary = {'natural': [], 'incremental': []}
  for i, data_leitura in enumerate(datas_disponiveis):
      vazoes = _get_vazoes_acomph(acomph_document, data_leitura)
      vazoes = build_vazoes_completo(vazoes, postos_artificiais, data_leitura, 'acomph')

      dictionary['natural'].append({'data': data_leitura})
      dictionary['natural'][i].update({key:value['natural'] for (key,value) in vazoes.items()})
      
      dictionary['incremental'].append({'data': data_leitura})
      dictionary['incremental'][i].update({key:value['incremental'] for (key,value) in vazoes.items()})
  
  return dictionary



def _add_ena_to_vazoes(vazoes, postos_document):
  for posto in vazoes:
    vazoes[posto].update({
      'ena': round(vazoes[posto]['natural']*postos_document[posto]['produtibilidade'],2)
    })
  return vazoes

def _build_enas_dict(acomph_document, postos_document):
    datas_disponiveis = _get_available_dates(acomph_document)
    postos_artificiais = get_postos_artificiais(postos_document)

    ena_dictionary = {}
    for data_leitura in datas_disponiveis:
        vazoes = _get_vazoes_acomph(acomph_document, data_leitura)
        vazoes = build_vazoes_completo(vazoes, postos_artificiais, data_leitura, 'acomph')

        vazoes = _add_ena_to_vazoes(vazoes, postos_document)
        ena_dictionary.update({data_leitura: {key:value['ena'] for (key,value) in vazoes.items()}})
    return ena_dictionary

def get_postos_submercado(postosDocument, submercado):
  return dict(
    filter(
      lambda elem: elem[1]['submercado'] == submercado, postosDocument.items()
    )
  )

def get_postos_bacia(postosDocument, bacia):
  return dict(
    filter(
      lambda elem: elem[1]['bacia'] == bacia, postosDocument.items()
    )
  )


def switch_postos(selector, postos_document):
  switcher = {
    # SUBMERCADOS
    "SE": get_postos_submercado(postos_document, selector),
    "S": get_postos_submercado(postos_document, selector),
    "NE": get_postos_submercado(postos_document, selector),
    "N": get_postos_submercado(postos_document, selector),
    # SUDESTE
    "GRANDE": get_postos_bacia(postos_document, selector),
    "PARANAÍBA": get_postos_bacia(postos_document, selector),
    "ALTO TIETÊ": get_postos_bacia(postos_document, selector),
    "TIETÊ": get_postos_bacia(postos_document, selector),
    "PARANAPANEMA (SE)": get_postos_bacia(postos_document, selector),
    "ALTO PARANÁ": get_postos_bacia(postos_document, selector),
    "BAIXO PARANÁ": get_postos_bacia(postos_document, selector),
    "PARAÍBA DO SUL*": get_postos_bacia(postos_document, selector),
    "ITABAPOANA": get_postos_bacia(postos_document, selector),
    "MUCURI": get_postos_bacia(postos_document, selector),
    'STA. MARIA DA VITÓRIA':get_postos_bacia(postos_document, selector),
    "DOCE": get_postos_bacia(postos_document, selector),
    "PARAGUAI": get_postos_bacia(postos_document, selector),
    "JEQUITINHONHA (SE)": get_postos_bacia(postos_document, selector),
    "AMAZONAS (SE)": get_postos_bacia(postos_document, selector),
    "SÃO FRANCISCO (SE)": get_postos_bacia(postos_document, selector),
    "TOCANTINS (SE)": get_postos_bacia(postos_document, selector),
    # SUL
    'IGUAÇU': get_postos_bacia(postos_document, selector),
    'JACUÍ': get_postos_bacia(postos_document, selector),
    'URUGUAI': get_postos_bacia(postos_document, selector),
    'ITAJAÍ-AÇU': get_postos_bacia(postos_document, selector),
    'PARANAPANEMA (S)': get_postos_bacia(postos_document, selector),
    'CAPIVARI': get_postos_bacia(postos_document, selector),
    # NORDESTE
    'SÃO FRANCISCO (NE)': get_postos_bacia(postos_document, selector),
    'JEQUITINHONHA (NE)': get_postos_bacia(postos_document, selector),
    'PARNAÍBA': get_postos_bacia(postos_document, selector),
    'PARAGUAÇU': get_postos_bacia(postos_document, selector),
    # NORTE
    'TOCANTINS (N)': get_postos_bacia(postos_document, selector),
    'AMAZONAS (N)': get_postos_bacia(postos_document, selector),
    'ARAGUARI': get_postos_bacia(postos_document, selector),
    'XINGU': get_postos_bacia(postos_document, selector)
  }
  return switcher.get(selector, "Invalid selector")

def _sum_ena(enas_dict, lista_postos, data):
  return round(sum([enas_dict[data][key] for key in lista_postos if key in enas_dict[data].keys()]),3) 

def _get_lista_enas(enas_dict, postos_document):
  lista_enas = []
  for data in enas_dict:
    dicionario = {
      'data': data,
      'SE': _sum_ena(enas_dict, switch_postos('SE', postos_document), data),
      'S': _sum_ena(enas_dict, switch_postos('S', postos_document), data),
      'NE': _sum_ena(enas_dict, switch_postos('NE', postos_document), data),
      'N': _sum_ena(enas_dict, switch_postos('N', postos_document), data),
      ## SUDESTE
      'GRANDE': _sum_ena(enas_dict, switch_postos('GRANDE', postos_document), data),
      'PARANAIBA': _sum_ena(enas_dict, switch_postos('PARANAÍBA', postos_document), data),
      'ALTO_TIETE': _sum_ena(enas_dict, switch_postos('ALTO TIETÊ', postos_document), data),
      'TIETE': _sum_ena(enas_dict, switch_postos('TIETÊ', postos_document), data),
      'PARANAPANEMA_SE': _sum_ena(enas_dict, switch_postos('PARANAPANEMA (SE)', postos_document), data),
      'ALTO_PARANA': _sum_ena(enas_dict, switch_postos('ALTO PARANÁ', postos_document), data),
      'BAIXO_PARANA': _sum_ena(enas_dict, switch_postos('BAIXO PARANÁ', postos_document), data),
      'PARAIBA_SUL': _sum_ena(enas_dict, switch_postos('PARAÍBA DO SUL*', postos_document), data),
      'ITABAPOANA': _sum_ena(enas_dict, switch_postos('ITABAPOANA', postos_document), data),
      'MUCURI': _sum_ena(enas_dict, switch_postos('MUCURI', postos_document), data),
      'STA_MARIA_DA_VITORIA': _sum_ena(enas_dict, switch_postos('STA. MARIA DA VITÓRIA', postos_document), data),
      'DOCE': _sum_ena(enas_dict, switch_postos('DOCE', postos_document), data),
      'PARAGUAI': _sum_ena(enas_dict, switch_postos('PARAGUAI', postos_document), data),
      'JEQUITINHONHA': _sum_ena(enas_dict, switch_postos('JEQUITINHONHA (SE)', postos_document), data),
      'AMAZONAS_SE': _sum_ena(enas_dict, switch_postos('AMAZONAS (SE)', postos_document), data),
      'SFRANCISCO_SE': _sum_ena(enas_dict, switch_postos('SÃO FRANCISCO (SE)', postos_document), data),
      'TOCANTINS_SE': _sum_ena(enas_dict, switch_postos('TOCANTINS (SE)', postos_document), data),
      ## SUL
      'IGUACU': _sum_ena(enas_dict, switch_postos('IGUAÇU', postos_document), data),
      'JACUI': _sum_ena(enas_dict, switch_postos('JACUÍ', postos_document), data),
      'URUGUAI': _sum_ena(enas_dict, switch_postos('URUGUAI', postos_document), data),
      'ITAJAI_ACU': _sum_ena(enas_dict, switch_postos('ITAJAÍ-AÇU', postos_document), data),
      'PARANAPANEMA_S': _sum_ena(enas_dict, switch_postos('PARANAPANEMA (S)', postos_document), data),
      'CAPIVARI': _sum_ena(enas_dict, switch_postos('CAPIVARI', postos_document), data),
      ## NORDESTE
      'SFRANCISCO_NE': _sum_ena(enas_dict, switch_postos('SÃO FRANCISCO (NE)', postos_document), data),
      'JEQUITINHONHA_NE': _sum_ena(enas_dict, switch_postos('JEQUITINHONHA (NE)', postos_document), data),
      'PARNAIBA': _sum_ena(enas_dict, switch_postos('PARNAÍBA', postos_document), data),
      'PARAGUACU': _sum_ena(enas_dict, switch_postos('PARAGUAÇU', postos_document), data),
      ## NORTE
      'TOCANTINS_N': _sum_ena(enas_dict, switch_postos('TOCANTINS (N)', postos_document), data),
      'AMAZONAS_N': _sum_ena(enas_dict, switch_postos('AMAZONAS (N)', postos_document), data),
      'ARAGUARI': _sum_ena(enas_dict, switch_postos('ARAGUARI', postos_document), data),
      'XINGU': _sum_ena(enas_dict, switch_postos('XINGU', postos_document), data),
    }
    dicionario.update(enas_dict[data])
    lista_enas.append(dicionario)
  return lista_enas

def build_enas_acomph(acomph_document, postos_document):
  ## Construindo um dicionário de ENAs
  enas_dict = _build_enas_dict(acomph_document, postos_document)
  
  ## Construindo uma lista contendo as ENAS de cada dia
  enas_list = _get_lista_enas(enas_dict, postos_document)
  return enas_list

def get_dicionario_enas(acomph, postos_document, postos_artificiais):
  dict_vazoes = build_vazoes_dict(acomph, postos_artificiais)
  lista_enas = build_enas_acomph(acomph, postos_document)
  return {
    'dataDocumento': acomph['fileDate'],
    'enas': lista_enas,
    'vazoes': dict_vazoes
    }

def calculaEnaPorREE(files):
    dfPostos = pd.DataFrame(files['postos_document']).T.reset_index()
    dfPostos = dfPostos.rename(columns={'index': 'idPosto'})[['idPosto', 'resEquivalente', 'tipo', 'nome', 'bacia', 'submercado', 'produtibilidade']]
    dfVazao = pd.DataFrame(files['ana_novo']['vazoes']['natural'])
    dfVazao = dfVazao.set_index("data").T.reset_index().rename(columns={'index': 'idPosto'})
    dfInfoVazao = dfPostos.merge(dfVazao, on='idPosto')

    produtibilidade = dfInfoVazao['produtibilidade'].values
    dfInfoVazao = dfInfoVazao.set_index(['idPosto', 'nome', 'bacia', 'submercado', 'tipo',  'resEquivalente', 'produtibilidade'])

    ### CALCULO REE ITAIPU (266 - 34 - 61 - 243) - * PRODUTIBILIDADE DE 66
    values_itaipu = dfInfoVazao[dfInfoVazao.index.get_level_values(0) == 266].values - dfInfoVazao[dfInfoVazao.index.get_level_values(0) == 34].values - dfInfoVazao[dfInfoVazao.index.get_level_values(0) == 61].values - dfInfoVazao[dfInfoVazao.index.get_level_values(0) == 243].values
    dfInfoVazao.loc[dfInfoVazao.index.get_level_values(0) == 66] = values_itaipu

    dfInfoEna = dfInfoVazao.mul(produtibilidade, axis=0)
    dfEnaREE = dfInfoEna.groupby(level=["resEquivalente"]).sum()

    produtibilidade_itaipu = dfInfoVazao[dfInfoVazao.index.get_level_values(0) == 66].reset_index()['produtibilidade'].values[0]

    ### CALCULO PARANAPANEMA - CALCULO PADRAO DEPOIS VAZAO DE 61 * PRODUTIBILIDADE 66
    dfIncrementoParanapanema = dfInfoVazao[dfInfoVazao.index.get_level_values(0) == 61] * produtibilidade_itaipu
    dfIncrementoParanapanema = dfIncrementoParanapanema.reset_index().set_index(['resEquivalente'])
    dfIncrementoParanapanema = dfIncrementoParanapanema.drop(columns=['idPosto', 'nome', 'bacia', 'submercado', 'tipo', 'produtibilidade'])
    dfEnaREE[dfEnaREE.index.get_level_values(0) == 12] = dfEnaREE[dfEnaREE.index.get_level_values(0) == 12] + dfIncrementoParanapanema

    ### CALCULO PARANA - CALCULO PADRAO DEPOIS VAZAO DE (43 + 34) * PRODUTIBILIDADE 66
    dfIncrementoParana = dfInfoVazao[dfInfoVazao.index.get_level_values(0).isin([43, 34])].reset_index().drop(columns=['idPosto', 'nome', 'bacia', 'submercado', 'tipo', 'produtibilidade']).groupby(['resEquivalente']).sum(numeric_only=True) * produtibilidade_itaipu
    dfEnaREE[dfEnaREE.index.get_level_values(0) == 10] = dfEnaREE[dfEnaREE.index.get_level_values(0) == 10] + dfIncrementoParana
    
    return dfEnaREE.round(2)

def edit_payload(files):
    lista_payload = []
    dfEnaREE = calculaEnaPorREE(files)
    for dado in files['ana_novo']['enas']:
        dct_submercado = {}
        dct_bacia={}
        dct_posto={}
        for key in dado.keys():
            if key =='SE' or key =='S' or key =='N' or key =='NE':
                dct_submercado.update({
                    key:dado[key]
                })
            elif type(key) == int:
                dct_posto.update({
                    key:dado[key]
                })
            elif key != 'data':
                dct_bacia.update({
                    key:dado[key]
                })
        dct={
            'data':dado['data'],
            'submercado':dct_submercado,
            'bacia':dct_bacia,
            'posto':dct_posto,
            'REE': dfEnaREE[dado['data']].to_dict()
        }
        lista_payload.append(dct)
    
    return lista_payload

############################################################## FUNCOES PARA LEITURA DO IPDO ##################################################################
def get_dataframe_hidrologicos(excel_io):
  df = pd.read_excel(excel_io, sheet_name = 'IPDO', usecols=range(10,24), skiprows=58, nrows= 13).fillna('')
  df.columns = range(df.shape[1])
  df = df.drop([1,3,8,10,12], axis='columns')
  df.columns=list(range(9))
  return df

def get_dict_dados_hidrologicos(LAKE,key_name):    
    s3_file = io.BytesIO(utils_s3.get_obj_from_s3(LAKE, key_name))
    
    df = get_dataframe_hidrologicos(s3_file)
    SE = list(df.loc[5].to_numpy())[1:] + list(df.loc[12].to_numpy())[1:3]
    S = list(df.loc[4].to_numpy())[1:] + list(df.loc[11].to_numpy())[1:3]
    NE = list(df.loc[3].to_numpy())[1:] + list(df.loc[10].to_numpy())[1:3]
    N = list(df.loc[2].to_numpy())[1:] + list(df.loc[9].to_numpy())[1:3]
    return {
        'SE': {'ENA_MWmed': SE[0],'ENA_bruta': SE[1], 'ENA_armazenada': SE[2], 'EAR_dia': SE[3],'EAR_dia_percentual': SE[4], 'EAR_desvio': SE[5], 'variacao_percentual': SE[6], 'variacao': SE[7]
        ,'cap_max': SE[8], 'variacao_mensal': SE[9]},
        'S': {'ENA_MWmed': S[0],'ENA_bruta': S[1], 'ENA_armazenada': S[2], 'EAR_dia': S[3],'EAR_dia_percentual': S[4], 'EAR_desvio': S[5], 'variacao_percentual': S[6], 'variacao': S[7]
        ,'cap_max': S[8], 'variacao_mensal': S[9]},
        'NE': {'ENA_MWmed': NE[0],'ENA_bruta': NE[1], 'ENA_armazenada': NE[2], 'EAR_dia': NE[3],'EAR_dia_percentual': NE[4], 'EAR_desvio': NE[5], 'variacao_percentual': NE[6], 'variacao': NE[7]
        ,'cap_max': NE[8], 'variacao_mensal': NE[9]},
        'N':{'ENA_MWmed': N[0],'ENA_bruta': N[1], 'ENA_armazenada': N[2], 'EAR_dia': N[3],'EAR_dia_percentual': N[4], 'EAR_desvio': N[5], 'variacao_percentual': N[6], 'variacao': N[7]
        ,'cap_max': N[8], 'variacao_mensal': N[9]}
    }