import pandas as pd
"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo renovaveis.dat do deck dessem
"""

def escrever_blocos(bloco_renovaveis):
    """
    Escreve o arquivo renovaveis.dat a partir dos blocos do df de cada um dos blocos do arquivo
    
    """
    def write_cabecalho_bloco_1():
        return """&XXXXXX;XXXXX ;XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX ;XXXXXXXXXX ;XXX ;X;\n&      ;CODIGO;NOME: Usina, Barra e Tipo de Usina       ;PMAX       ;FCAP;C;\n&XXXXXX;XXXXX ;XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX ;XXXXXXXXXX ;XXX ;X;\n"""

    def write_cabecalho_bloco_2():
        return """\n&XXXXXXXXXX ;XXXXX ;XXXXX ;
&           ;CODIGO;BARRA ;
&XXXXXXXXXX ;XXXXX ;XXXXX ;\n"""

    def write_cabecalho_bloco_3():
        return """\n&XXXXXXXXXX;XXXXX ;XX ;
&          ;CODIGO;SBM;
&XXXXXXXXXX;XXXXX ;XX ;\n"""

    def write_cabecalho_bloco_geracao():
        return """\n&XXXXXXXXXXXXXX;XXXXX ;XX ;XX ;X ;XX ;XX ;X ;XXXXXXXXXX ;
&              ;CODIGO;       DATA          ;   GERACAO ;
&XXXXXXXXXXXXXX;XXXXX ;XX ;XX ;X ;XX ;XX ;X ;XXXXXXXXXX ;\n"""
    #ESCREVENDO BLOCO 1
    df=bloco_renovaveis['bloco_1']
    df['MEIO'] = df.apply(lambda x:f"_{x['usina']}_{x['letra']}_{x['barra_inteiro']}_{x['barra']}_{x['tipo']}" if x['letra']!="" else f"_{x['usina']}_{x['barra']}_{x['tipo']}",axis=1)
    df['EOLICA'] = 'EOLICA'
    df = df[['EOLICA','codigo','nome','MEIO','potencia_max','fator_capacidade','flag']]

    fmt = '{:7s};{:>5s} ;{:<6s}{:<35s};{:>10s} ;{:3s} ;{:1s}; '

    rows = [tuple(r) for r in df.reset_index(drop=True).values]
    texto = write_cabecalho_bloco_1()+'\n'.join(fmt.format(*r) for r in rows)

    #ESCREVENDO BLOCO 2
    df=bloco_renovaveis['bloco_2']
    df['TIPO'] = 'EOLICABARRA'
    df = df[['TIPO','codigo','barra']]

    fmt = '{:11s} ;{:>5s} ;{:0>5s} ;'
    rows = [tuple(r) for r in df.reset_index(drop=True).values]
    texto = texto+write_cabecalho_bloco_2()+'\n'.join(fmt.format(*r) for r in rows)

    #ESCREVENDO BLOCO submercado
    df=bloco_renovaveis['bloco_submercado']
    df['TIPO'] = 'EOLICASUBM'
    df = df[['TIPO','codigo','submercado']]

    fmt = '{:10s} ;{:>5s} ;{:<2s} ;'
    rows = [tuple(r) for r in df.reset_index(drop=True).values]
    texto = texto+write_cabecalho_bloco_3()+'\n'.join(fmt.format(*r) for r in rows)

    #ESCREVENDO BLOCO GERACAO
    df=bloco_renovaveis['bloco_geracao']
    df['TIPO'] = 'EOLICA-GERACAO'
    df = df[['TIPO','codigo','dia_inicio','hora_inicio','semi_hora_inicio','dia_fim','hora_fim','semi_hora_fim','geracao']]

    fmt = '{:<15s};{:>5s} ;{:>2s} ;{:>2s} ;{:>1s} ;{:>2s} ;{:>2s} ;{:>1s} ;{:>10s} ;'
    rows = [tuple(r) for r in df.reset_index(drop=True).values]
    '\n'.join(fmt.format(*r) for r in rows)
    texto = texto+write_cabecalho_bloco_geracao()+'\n'.join(fmt.format(*r) for r in rows)
    return texto
    


def get_renovaveis_blocos(renovaveis_str: str,tipo_deck:str):
    """
    Retorna um dicionario em que os itens sao os diferentes blocos do renovaveis.dat

    """
    bloco_1 = []
    bloco_2 = []
    bloco_geracao = []
    bloco_submercado = []

    for line in renovaveis_str.splitlines():
        if 'EOLICA ;' in line:
            if "_F_" in line:
                letra=True
            else:
                letra=False
            corrigirNome=""
            if 'CTV_ACARAU_I' in line:
                corrigirNome = 'CTV_ACARAU_I'
            elif 'ASS_ASSU V' in line:
                corrigirNome = 'ASS_ASSU V'
            elif 'Santa Luzia Dï¿½Oeste' in line:
                corrigirNome = 'Santa Luzia DOeste'
            bloco_1_dict = {
                'codigo': line.split(';')[1].strip(),
                'nome': line.split(';')[2].strip().split('_')[0].strip(),
                'usina': line.split(';')[2].strip().split('_')[1].strip() if corrigirNome=="" else corrigirNome,
                'letra': line.split(';')[2].strip().split('_')[2].strip() if letra else "",
                'barra_inteiro': line.split(';')[2].strip().split('_')[3].strip() if letra else "",
                'barra': line.split(';')[2].strip().split('_')[-2].strip(),
                'tipo': line.split(';')[2].strip().split('_')[-1].strip(),
                'potencia_max': line.split(';')[-4].strip(),
                'fator_capacidade': line.split(';')[-3].strip(),
                'flag': line.split(';')[-2].strip(),
            }
            bloco_1.append(bloco_1_dict)
        
        elif 'EOLICABARRA ;' in line:

            bloco_2_dict = {
                'codigo': line.split(';')[1].strip(),
                'barra': str(int(line.split(';')[2].strip())),
            }
            bloco_2.append(bloco_2_dict)
        
        elif 'EOLICA-GERACAO ;' in line:

            bloco_geracao_dict = {
                'codigo': line.split(';')[1].strip(),
                'dia_inicio': line.split(';')[2].strip(),
                'hora_inicio': line.split(';')[3].strip(),
                'semi_hora_inicio': line.split(';')[4].strip(),
                'dia_fim': line.split(';')[5].strip(),
                'hora_fim': line.split(';')[6].strip(),
                'semi_hora_fim': line.split(';')[7].strip(),
                'geracao': line.split(';')[8].strip(),
            }

            bloco_geracao.append(bloco_geracao_dict)

        elif 'EOLICASUBM ;' in line:
            
            bloco_submercado_dict = {
                'codigo': line.split(';')[1].strip(),
                'submercado': line.split(';')[2].strip()
            }
            bloco_submercado.append(bloco_submercado_dict)

    if tipo_deck == 'ccee':
        return {
            'bloco_1': pd.DataFrame(bloco_1),
            'bloco_2': pd.DataFrame(bloco_2),
            'bloco_submercado': pd.DataFrame(bloco_submercado),
            'bloco_geracao': pd.DataFrame(bloco_geracao)
        }
    else:
        df_bloco1 = pd.DataFrame(bloco_1)
        df_bloco1['flag'] = '0' #zerando as flags para o caso ons

        return {
            'bloco_1': df_bloco1,
            'bloco_2': pd.DataFrame(bloco_2),
            'bloco_submercado': pd.DataFrame(bloco_submercado),
            'bloco_geracao': pd.DataFrame(bloco_geracao)
        }
    