"""
Modulo desenhado para conter as classes e funcoes relacionadas aos estudos de 
 decks encadeados.
"""

import os
import zipfile as zp


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
    file_name = file_content[1].split('.')[0]
    deck_name = file_content[0]

    D[deck_name].update({file_name.lower(): file_path})
  return D