import datetime
import os
import pandas as pd
from . import utils_gsheets

import boto3

def get_pld_db(ano_deck):
  dynamodb = boto3.resource('dynamodb', region_name='sa-east-1')
  table = dynamodb.Table('pld-valor')
  print('Extraindo dados do dynamo')
  response = table.get_item(
      Key={
          'ano':ano_deck
      }
  )
  item = response['Item']
  piso = float(item['min'])
  estrutural = float(item['max_estrutural'])

  return piso, estrutural

def adjust_teto_piso(valor, piso, teto):
  """
  # ========================================================================================= #
  #  Ajusta um float representando um custo marginal de operação para um valor correspondente #
  #   em PLD. Ou seja, se cmo <= pld_min, cmo = pld_min. se cmo >= pld_max, cmo = pld_max     #
  # ========================================================================================= #
  """
  if type(valor) not in [float, int]:
    raise Exception("'adjust_teto_piso' can only receive a numerical value, float or int")

  if valor >= teto:
    valor = teto
  elif valor <= piso:
    valor = piso
  else:
    valor = valor
  return valor

def get_patamares_horarios(ano):
  """
  # ============================================================================================ #
  #  Returna um dicionario com os patamares horarios de cada um dos dias de cada mes.            #
  #   {                                                                                          #
  #     'jan': {                                                                                 #
  #       '2020-1-1': [                                                                          #
  #         'hora': int,                                                                         #
  #         'dia_semana': str,                                                                   #
  #         'patamar': str,                                                                      #
  #         'tipo_horario': str,                                                                 #
  #         'tipo': str                                                                          #
  #       ]                                                                                      #
  #     },                                                                                       # 
  #      .                                                                                       #
  #      .                                                                                       #
  #      .                                                                                       #
  #     ,                                                                                        #
  #     'dez': {...},                                                                            #
  #   }                                                                                          #
  # ============================================================================================ #
  """
  patamares_gsheet = utils_gsheets.get_workheet_records('AAC001',  str(ano))
  df_patamares = pd.DataFrame(patamares_gsheet)

  translationTable = str.maketrans("éáàèùâêîôûç", "eaaeuaeiouc")
  dict_patamares = {
    'jan': {},
    'fev': {},
    'mar': {},
    'abr': {},
    'mai': {},
    'jun': {},
    'jul': {},
    'ago': {},
    'set': {},
    'out': {},
    'nov': {},
    'dez': {},
  }

  for item in df_patamares.itertuples():
    mes = item[2].lower()[:3]
    dia = datetime.datetime.strptime(item[3], '%d/%m/%Y').date()
    hora = int(item[4].split(':')[0])
    patamar = item[5].lower().translate(translationTable)
    tipo_horario = item[6].lower().translate(translationTable)
    dia_semana = item[7].lower().translate(translationTable)
    tipo = item[8].lower()
    if dict_patamares[mes].get(dia.strftime('%Y-%m-%d')) == None:
      dict_patamares[mes].update(
        {dia.strftime('%Y-%m-%d'): []}
      )
    dict_patamares[mes][dia.strftime('%Y-%m-%d')].append({
      'hora': hora,
      'dia_semana': dia_semana,
      'patamar': patamar,
      'tipo_horario': tipo_horario,
      'tipo': tipo
    })
  return dict_patamares