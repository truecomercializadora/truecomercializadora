
import json

from . import (
    utils_http, utils_files,utils_s3
)

import pandas as pd
import io

"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo cadic.dat
"""

Usinas = ['ITAIPU','ITAIPU','ITAIPU','ITAIPU','ITAIPU','ITAIPU','ANDE','ANDE','ANDE','ANDE','ANDE','ANDE']

def comparaCadic(cadic_str_A, cadic_str_B):
    '''
    Transcreve as strings A e B para dataframes de valores inteiros e efetua a comparação entre elas
    '''
    bloco_1_A = (utils_files.select_document_parts(cadic_str_A,'CONS.ITAIPU','ANDE'))[0].splitlines()
    str_bloco1_A = '\n'.join(bloco_1_A[1:7])
    df1 = pd.read_fwf(io.StringIO(str_bloco1_A),names=['XXXJAN.','XXXFEV.','XXXMAR.','XXXABR.','XXXMAI.','XXXJUN.','XXXJUL.','XXXAGO.','XXXSET.','XXXOUT.','XXXNOV.','XXXDEZ.'])
    bloco_2_A = (utils_files.select_document_parts(cadic_str_A,'ANDE',cadic_str_A.splitlines()[-1]))[0].splitlines()
    str_bloco2 = '\n'.join(bloco_2_A[1:7])
    df2 = pd.read_fwf(io.StringIO(str_bloco2),names=['XXXJAN.','XXXFEV.','XXXMAR.','XXXABR.','XXXMAI.','XXXJUN.','XXXJUL.','XXXAGO.','XXXSET.','XXXOUT.','XXXNOV.','XXXDEZ.'])
    df_comp1 = pd.concat([df1,df2]).fillna(0)


    bloco_1_B = (utils_files.select_document_parts(cadic_str_B,'CONS.ITAIPU','ANDE'))[0].splitlines()
    str_bloco1_B = '\n'.join(bloco_1_B[1:7])
    df1 = pd.read_fwf(io.StringIO(str_bloco1_B),names=['XXXJAN.','XXXFEV.','XXXMAR.','XXXABR.','XXXMAI.','XXXJUN.','XXXJUL.','XXXAGO.','XXXSET.','XXXOUT.','XXXNOV.','XXXDEZ.'])
    bloco_2_B = (utils_files.select_document_parts(cadic_str_B,'ANDE',cadic_str_B.splitlines()[-1]))[0].splitlines()
    str_bloco2 = '\n'.join(bloco_2_B[1:7])
    df2 = pd.read_fwf(io.StringIO(str_bloco2),names=['XXXJAN.','XXXFEV.','XXXMAR.','XXXABR.','XXXMAI.','XXXJUN.','XXXJUL.','XXXAGO.','XXXSET.','XXXOUT.','XXXNOV.','XXXDEZ.'])
    df_comp2 = pd.concat([df1,df2]).fillna(0)

    return df_comp1.round().astype(int), df_comp2.round().astype(int)

def ComparacaoCadic(df_comp1, df_comp2):
    '''
    Efetua a comparacao das dataframes, caso existam diferenças entre
    df1 e df2, realiza a subtração entre elas para adicionar a df de comparação ao payload
    '''
    try:
        if(df_comp1.equals(df_comp2)):
            message = 'Não há diferença entre os decks'
            df_comp1['USINAS'] = Usinas
            lista=[df_comp1.reset_index().rename(columns={"index": "ANO"}).to_dict(orient='records')]
            payload_body = io.BytesIO(json.dumps(lista).encode())
            print(message)
            return payload_body
        else:
            message = 'Há diferença entre os decks'
            print(message)
            df_differences = df_comp2.subtract(df_comp1)
            df_differences['USINAS'] = Usinas
            df_comp1['USINAS'] = Usinas
            df_comp2['USINAS'] = Usinas
            lista=[df_comp1.reset_index().rename(columns={"index": "ANO"}).to_dict(orient='records'),df_comp2.reset_index().rename(columns={"index": "ANO"}).to_dict(orient='records'),df_differences.reset_index().rename(columns={"index": "ANO"}).to_dict(orient='records')]
            payload_body = io.BytesIO(json.dumps(lista).encode())
            return payload_body

    except Exception as error:
            print(error.args)
            return utils_http.server_error_response(500, "Erro na comparacao")