import io
import json
import numpy as np
import pandas as pd

from . import utils_files

def get_data(pmo_str):
  """
  Retorna uma string %Y-%m-%d representando a data do deck em estudo a partir do pmo.dat
  """
  if type(pmo_str) != str:
    raise Exception("'get_data_deck' can only receive a pmo.dat string.")
      
  if 'MES INICIAL DO PERIODO DE ESTUDO' not in pmo_str:
    raise Exception("'get_data_deck' input str does not seem to represent a pmo.dat file. Verify the input content.")

  begin = 'MES INICIAL DO PERIODO DE ESTUDO'
  end = 'NUMERO DE ANOS QUE PRECEDEM O HORIZONTE DE ESTUDO'

  mes,ano = (data.strip().split()[-1] for data in utils_files.select_document_part(pmo_str, begin, end).splitlines() if data.strip() != '')
  return '{}-{}-1'.format(ano, mes)

def get_usina_modif(modif_str: str, id_usina: int) -> str:
  """
  Retorna uma string com todas as informacoes de uma determinada usina no
  modif.dat.
  """
  if type(modif_str) != str:
    raise Exception("'get_usina_modif' can only receive a modif.dat string.")

  if 'P.CHAVE  MODIFICACOES E INDICES' not in modif_str:
    raise Exception("'get_usina_modif' input str does not seem to represent a "\
                    "modif.dat file. Verify the input content.")
  
  if type(id_usina) != int:
    raise Exception("'get_usina_modif' can only receive an integer for usina "\
                    "type")

  begin = ' USINA    {:>3}'.format(id_usina)
  end = ' USINA'

  return utils_files.select_document_part(modif_str, begin, end)


def get_enas(pmo_str):
  """
  Retorna um dicionario contendo as enas (mes a mes) a partir da string de um pmo.dat
  """
  if type(pmo_str) != str:
    raise Exception("'get_enas' can only receive a pmo.dat string.")
      
  if 'ENERGIAS AFLUENTES PASSADAS EM REFERENCIA A PRIMEIRA CONFIGURACAO DO SISTEMA CONSIDERANDO CANAL DE FUGA MEDIO' not in pmo_str:
    raise Exception("'get_enas' input str does not seem to represent a pmo.dat file. Verify the input content.")

  begin = 'ENERGIAS AFLUENTES PASSADAS EM REFERENCIA A PRIMEIRA CONFIGURACAO DO SISTEMA CONSIDERANDO CANAL DE FUGA MEDIO'
  end = 'MODELO ESTRATEGICO DE GERACAO HIDROTERMICA A SUBSISTEMAS'
  lines = utils_files.select_document_part(pmo_str, begin, end).splitlines()
  
  return {
    content.split()[0].replace('SUDESTE', 'SE').replace('SUL', 'S').replace('NORDESTE', 'NE').replace('NORTE', 'N'): [float(n.replace('-', '0')) for n in content.split()[1:]]
    for content in [line for line in lines][4:-4]
  }


def get_enas_submercados(pmo_str):
  """
  Retorna um dicionario contendo as enas (mes a mes) a partir da string de um pmo.dat
  """
  if type(pmo_str) != str:
    raise Exception("'get_enas_submercados' can only receive a pmo.dat string.")
      
  if 'ENERGIAS AFLUENTES PASSADAS EM REFERENCIA A PRIMEIRA CONFIGURACAO DO SISTEMA CONSIDERANDO CANAL DE FUGA MEDIO' not in pmo_str:
    raise Exception("'get_enas_submercados' input str does not seem to represent a pmo.dat file. Verify the input content.")

  enas = get_enas(pmo_str)
  return {
    'SE': [round(sum(x),2) for x in zip(enas['SE'], enas['MADEIRA'], enas['TPIRES'], enas['ITAIPU'], enas['PARANA'], enas['PRNPANEMA'])],
    'S': [round(sum(x),2) for x in zip(enas['S'], enas['IGUACU'])],
    'NE': enas['NE'],
    'N':[round(sum(x),2) for x in zip(enas['N'], enas['BMONTE'], enas['MAN-AP'])]
  }


def get_enas_percentuais_fechamento(pmo_str, mlts):
  """
  Retorna um dicionario contendo as enas de fechamento (em percentual da mlt), a partir  
   do pmo.dat (em string) e do dicionário contendo as mlts. O dicionario de mlts por sub-
   mercado deve ser obtido atraves da funcao 'get_mlts()', disponivel no modulo 'ons'    
  """
  if type(pmo_str) != str:
    raise Exception("'get_enas_percentuais_fechamento' can only receive a pmo.dat string.")

  if 'ENERGIAS AFLUENTES PASSADAS EM REFERENCIA A PRIMEIRA CONFIGURACAO DO SISTEMA CONSIDERANDO CANAL DE FUGA MEDIO' not in pmo_str:
    raise Exception("'get_enas_percentuais_fechamento' input str does not seem to represent a pmo.dat file. Verify the input content.")
      
  if type(mlts) != dict:
    raise Exception("'get_enas' can only receive 'mlts' as a dictionary. 'mlts' of type {} detected".format(mlts))
  
  ena_fechamento = get_enas_submercados(pmo_str)
  D = {"SE": [], "S": [], "NE": [], "N": []}
  for subsistema in ena_fechamento.keys():
    mlt_subsistema = mlts[subsistema]
    for i, ena in enumerate(ena_fechamento[subsistema]):
      idx_mes = str(i+1)
      ena_percentual_mlt =  round(ena/mlt_subsistema[idx_mes],3)
      D[subsistema].append(ena_percentual_mlt)
  return D


def get_ear_inicial(pmo_str):
  """
  Retorna um dicionario de dicionarios contendo as energias armazenadas iniciais de cada 
   subsistema. Cada dicionario contem a energia em MWmes, o percentual da Energia Armaze-
   nada maxima e a Energia Maxima armezanavel do subsistema.                             
  """
  
  if type(pmo_str) != str:
    raise Exception("'get_ear_inicial' can only receive a pmo.dat string.")
    
  if ('ENERGIA ARMAZENADA INICIAL' not in pmo_str) or ('META DE GERACAO HIDRAULICA MINIMA' not in pmo_str):
    raise Exception("'get_ear_inicial' input str does not seem to represent a pmo.dat file. Verify the input content.")
  
  begin = 'ENERGIA ARMAZENADA INICIAL'
  end = 'META DE GERACAO HIDRAULICA MINIMA'
  lines = [line.replace('%','').split() for line in utils_files.select_document_part(pmo_str, begin, end).splitlines()[1:] if line.strip() != '']

  D = {}
  for item in np.array(lines).transpose():
    subsistema = item[0].replace('SUDESTE', 'SE').replace('SUL', 'S').replace('NORDESTE', 'NE').replace('NORTE', 'N')
    mw_mes = float(item[1])
    percentual_ear_max = round(float(item[2].replace('-','0'))/100,3)
    ear_max = round(mw_mes/percentual_ear_max,2) if percentual_ear_max != 0 else 0

    D.update({
      subsistema: {
        'mw_mes': mw_mes,
        'percentual_ear_max': percentual_ear_max,
        'ear_max': ear_max
      }
    })
  return D

def get_ear_inicial_percentual_por_submercado(pmo_str):
  """
  Retorna um dicionario contendo os percentuais (em relacao ao maximo) de Energia
   Armazenada Inicial em cada submercado. O dicionario eh montado a partir do
   dicionario de dicionarios obtido atraves da funcao 'get_ear_inicial' deste
   mesmo modulo.
  """
  
  if type(pmo_str) != str:
    raise Exception("'get_ear_inicial_percentual' can only receive a pmo.dat string.")
    
  if ('ENERGIA ARMAZENADA INICIAL' not in pmo_str) or ('META DE GERACAO HIDRAULICA MINIMA' not in pmo_str):
    raise Exception("'get_ear_inicial_percentual' input str does not seem to represent a pmo.dat file. Verify the input content.")
  
  # Inicializando o dicionario de dicionarios com todos os subsistemas
  ear_inicial = get_ear_inicial(pmo_str)

  ear_max_se = ear_inicial['SE']['ear_max'] + ear_inicial['MADEIRA']['ear_max'] + ear_inicial['TPIRES']['ear_max'] + ear_inicial['ITAIPU']['ear_max'] + ear_inicial['PARANA']['ear_max'] + ear_inicial['PRNPANEMA']['ear_max']
  ear_max_s = ear_inicial['S']['ear_max'] + ear_inicial['IGUACU']['ear_max']
  ear_max_ne = ear_inicial['NE']['ear_max']
  ear_max_n = ear_inicial['N']['ear_max'] + ear_inicial['BMONTE']['ear_max'] + ear_inicial['MAN-AP']['ear_max']

  return {
    'SE': round((ear_inicial['SE']['mw_mes'] + ear_inicial['MADEIRA']['mw_mes'] + ear_inicial['TPIRES']['mw_mes'] + ear_inicial['ITAIPU']['mw_mes'] + ear_inicial['PARANA']['mw_mes'] + ear_inicial['PRNPANEMA']['mw_mes'])/ear_max_se,3),
    'S': round((ear_inicial['S']['mw_mes'] + ear_inicial['IGUACU']['mw_mes'] )/ear_max_s,3),
    'NE': round((ear_inicial['NE']['mw_mes'])/ear_max_ne,3),
    'N': round((ear_inicial['N']['mw_mes'] + ear_inicial['BMONTE']['mw_mes'] + ear_inicial['MAN-AP']['mw_mes']) /ear_max_n,3)
  }

def get_expt_list(expt_str: str, ano_deck: int) -> list:
	"""
	Retorna uma lista de dicionarios representando cada uma das linhas do arquivo
	  expt.dat
	"""
	if type(expt_str) != str:
		raise TypeError("'get_expt_list' can only receive a expt.dat string.")

	if ('NUM   TIPO   MODIF  MI ANOI MF ANOF' not in expt_str):
		raise Exception("'get_expt_list' input str does not seem to represent a "
	                    "expt.dat file. Verify the input content.")

	if type(ano_deck) != int:
		raise TypeError("'get_expt_list' can only receive an integer for 'ano_deck'")

	return [{
		'numeroUsina': line[:5].strip(),
		'tipoModificacao': line[5:10].strip(),
		'novoValor': round(float(line[11:19].strip()),2),
		'mesInicio': int(line[20:22].strip()),
		'anoInicio': int(line[23:27].strip()),
		'mesFim': int(line[28:30].strip()) if line[28:30].strip() != '' else 12 ,
		'anoFim': int(line[31:35].strip()) if line[31:35].strip() != '' else int(ano_deck) + 4
	} for line in expt_str.splitlines()[2:]]

def write_expt_file(expt_df: pd.DataFrame) -> bytes:
	"""
	Retorna os bytes correspondentes a um arquivo expt.dat, escrito a partir do
	  dataframe de entrada.
	"""
	if type(expt_df) != pd.DataFrame:
		raise Exception("'write_expt_file' can only receive a pandas DataFrame")

	master_io = io.BytesIO()
	master_io.write('NUM   TIPO   MODIF  MI ANOI MF ANOF\r\n'.encode('latin-1'))
	master_io.write('XXXX XXXXX XXXXXXXX XX XXXX XX XXXX\r\n'.encode('latin-1'))
	for line in json.loads(expt_df.reset_index().to_json(orient='records')):
		master_io.write("{:>4d} {:>5} {:>8.2f} {:>2d} {:>4d} {:>2d} {:>4d}\r\n".format(
			int(line['numeroUsina']),
			line['tipoModificacao'],
			line['novoValor'],
			int(line['mesInicio']),
			int(line['anoInicio']),
			int(line['mesFim']),
			int(line['anoFim'])
		).encode('latin-1'))
	return master_io.getvalue()

