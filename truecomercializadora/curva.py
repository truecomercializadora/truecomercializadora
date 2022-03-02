from truecomercializadora import (utils_files)

import pandas as pd
import io


def get_block_curva(curva_str):
    '''
    Obtém o bloco custo da string do arquivo 'curva.dat'.
    '''
    str_end = ' 999'
    idx_end = curva_str.find(str_end)

    return '\r\n'.join(curva_str[:idx_end].splitlines()[2:])

def custoDF(custoStr):
    '''
    Retorna um dataframe com o bloco custo a partir da string do curva.dat 
    '''
    df1 = pd.read_fwf(io.StringIO(custoStr),skiprows=0)
    df1.drop(0, axis = 0, inplace=True)
    df1 = df1.set_index('SISTEMA')

    return df1.astype(float)

def curvaDF(curva):
    '''
    Retorna um dataframe com o bloco curva a partir da string do curva.dat resultante da função 'get_block_curva'
    '''
    new_lines = []
    submercados = []
    datas = []
    for line in curva:
        if line == ' ':
            break
        if line[0] == ' ' and line[3] != ' ':
            submercados.append(int(line))
            pass
        else:
            new_lines.append(line)
            if(line[0:4].isdigit()):
                datas.append(line[0:4])
    df1 = pd.read_fwf(io.StringIO('\r\n'.join(new_lines)))
    df1 = df1.rename(columns={'Unnamed: 0': 'Data', 'JAN.X': 'JAN', 'FEV.X': 'FEV', 'MAR.X':'MAR', 'ABR.X':'ABR','MAI.X':'MAI', 'JUN.X':'JUN', 'JUL.X':'JUL', 
    'AGO.X': 'AGO', 'SET.X': 'SET', 'OUT.X': 'OUT', 'NOV.X': 'NOV', 'DEZ.X': 'DEZ'})
    # df1 = df1.set_index('Data')
    df1.drop('Data',axis = 1, inplace=True)
    submercados_out = []
    for submercado in submercados:
        for i in range(5):
            submercados_out.append('{submercado}'.format(submercado=submercado) + ' - ' + str(datas[i]))
    
    df1['SUBMERCADO'] = submercados_out
    df1 = df1.set_index('SUBMERCADO')

    return df1.astype(float)


def comparaCurva(curva_strA, curva_strB):
    '''
    Tem como entrada a string de dois arquivos 'curva.dat' e retorna o curtoA,custoB,custo_diff,curvaA,curvaB,curva_diff.
    '''
    custoA = get_block_curva(curva_str=curva_strA)
    custoA = custoDF(custoA)

    custoB = get_block_curva(curva_str=curva_strB)
    custoB = custoDF(custoB)

    custo_diff = custoB.subtract(custoA, fill_value=0).reindex_like(custoB).astype(float)
    custo_diff = custo_diff[(custo_diff != 0).all(1)]

    curvaB = utils_files.select_document_part(curva_strB, "CURVA", "9999").splitlines()[2:]
    curvaB = curvaDF(curvaB)

    curvaA = utils_files.select_document_part(curva_strA, "CURVA", "9999").splitlines()[2:]
    curvaA = curvaDF(curvaA)

    curva_diff = curvaB.subtract(curvaA, fill_value=0).reindex_like(curvaB).astype(float)
    curva_diff = curva_diff[(curva_diff != 0).all(1)]

    return custoA.reset_index().astype(int), custoB.reset_index().astype(int), custo_diff.reset_index(), curvaA.astype(int).reset_index(), curvaB.astype(int).reset_index(), curva_diff.astype(int).reset_index()
