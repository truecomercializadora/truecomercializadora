"""
Modulo desenhado para conter as classes e funcoes relacionadas aos estudos de 
 decks encadeados.
"""

import datetime
import os
import zipfile as zp

from . import utils_datetime


def get_decks_estudo(estudo_zip: zp.ZipFile) -> dict:
	"""
	Um estudo pode ser composto por um ou mais decks. Estudos prospectivos sao
	em geral, compostos por pares mensais de decks. Um NEWAVE outro DECOMP. A
	funcao 'get_decks_estudo' retorna um dicionario contendo os decks dispo-
	niveis dentro do estudo, agrupados em 'decomp' ou 'newave'. 
	"""

	if type(estudo_zip) != zp.ZipFile:
		raise Exception("'get_estudo_files' should be a valid zipfile.ZipFile Class. "
                    "Input has type {}".format(type(estudo_zip)))

	return {
		'decomp': list({os.path.split(file)[0] for file in estudo_zip.namelist()
						if 'DC' in file}),
		'newave': list({os.path.split(file)[0] for file in estudo_zip.namelist()
						if 'NW' in file})
	}

def get_decks_por_data(estudo_zip: zp.ZipFile) -> dict:
    """
    Um estudo pode ser composto por um ou mais decks. Estudos prospectivos sao
      em geral, compostos por pares mensais de decks. Um NEWAVE outro DECOMP. A
      funcao 'get_decks_por_data' retorna um dicionario contendo os decks dispo-
      niveis dentro do estudo, agrupados pela data do deck. 
    """
    
    if type(estudo_zip) != zp.ZipFile:
        raise Exception("'get_decks_por_data' should be a valid zipfile.ZipFile "
                        "Class. Input has type {}".format(type(estudo_zip)))

    datas = list(set([os.path.split(file)[0].split('-')[0][2:] for file in estudo_zip.namelist()]))
    D = {}
    for data in datas:
        D.update({data: {}})
        deck_nw = {os.path.split(file)[0] for file in estudo_zip.namelist() if data in file and 'NW' in file}
        deck_dc = {os.path.split(file)[0] for file in estudo_zip.namelist() if data in file and 'DC' in file}
        if len(deck_nw)>0:
            D[data].update({"NW": list(deck_nw)[0]})
        if len(deck_dc)>0:
            D[data].update({"DC": list(deck_dc)[0]})
    return D

def get_estudo_files(estudo_zip: zp.ZipFile) -> dict:
  """
  E muito comum que seja necessario alterar ou acessar multiplos arquivos do
    mesmo tipo dentro de estudos, por exemplo para atualizar todos os arquivos
    dadger.dat dentro de um estudo. Para que isso seja feito de forma mais or-
    ganizada, a funcao 'get_estudo_files' retorna um dicionario contendo o ma-
    peamento de todos os arquivos disponiveis no deck e sua respectiva localiza-
    cao.
  """
  
  if type(estudo_zip) != zp.ZipFile:
    raise Exception("'get_estudo_files' should be a valid zipfile.ZipFile Class. "
                    "Input has type {}".format(type(estudo_zip)))
  
  D = {os.path.split(file_path)[0]: {} for file_path in estudo_zip.namelist()}
  # Inicializando um mapa de decks.     
  
  # Atualizando o mapeamento dos arquivos
  for file_path in estudo_zip.namelist():
    file_content = os.path.split(file_path)
    file_name = file_content[1].split('.')[0].lower()
    deck_name = file_content[0]

    D[deck_name].update({file_name.lower(): file_path})
  return D

def get_deck_names(refInicio:str, refHorizonte: str) -> dict:
    '''
    Retorna um dicionario com o nome dos decks, newave e decomp
     de todo o horizonte encadeado.
     
     :refInicio = data no formato 'YYYY-mm-rev'
     :refHorizonte = data no formato 'YYYY-mm-rev'
    '''
    if type(refInicio) != str or type(refHorizonte) != str:
      raise Exception("'get_deck_names' can only receive str inputs")

    if not refInicio.split('-')[2].isdigit():
      raise Exception("'refInicio' must have a valid 'REV' ")

    if int(refInicio.split('-')[2]) not in range(5):
      raise Exception("'refInicio' must have a valid 'rev' value between 1 and 4")

    if int(refInicio.split('-')[1]) not in range(1, 13):
      raise Exception("'refInicio' must have a valid 'rev' value between 1 and 4")

    if not refHorizonte.split('-')[2].isdigit():
      raise Exception("'refHorizonte' must have a valid integer 'rev' ")

    if int(refHorizonte.split('-')[2]) not in range(5):
      raise Exception("'refHorizonte' must have a valid 'rev' value between 1 and 4")

    if int(refHorizonte.split('-')[1]) not in range(1, 13):
      raise Exception("'refHorizonte' must have a valid 'rev' value between 1 and 4")

    # Decompondo as datas do deck de entrada e o deck final do horizonte
    begin_datetime = datetime.datetime(int(refInicio.split('-')[0]), int(refInicio.split('-')[1]), 1)

    end_rev = int(refHorizonte.split('-')[2])
    end_datetime = datetime.datetime(int(refHorizonte.split('-')[0]), int(refHorizonte.split('-')[1]), 1)

    if begin_datetime >= end_datetime:
      raise Exception("'refInicio' should be bigger than 'refHorizonte'")
    
    diff_months = utils_datetime.diff_month(end_datetime, begin_datetime)

    # Construindo o dicionario
    D = {'decomp': [], 'newave': []}
    deck_date = begin_datetime.date()
    for _ in range(1, diff_months + 1):
        deck_date = utils_datetime.add_one_month(deck_date)
        dc_name = 'DC{}{:02d}-sem{}'.format(deck_date.year, deck_date.month, end_rev+1)
        nw_name = 'NW{}{:02d}'.format(deck_date.year, deck_date.month)
        D['decomp'].append(dc_name)
        D['newave'].append(nw_name)
        
    return D