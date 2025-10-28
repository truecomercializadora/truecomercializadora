import boto3
import json
from . import utils_s3 

def enviar_modelo_preco(key_name : str, bucket_s3 :str, modo_execucao : int, titulo :str, tags:list, max_inviabilidades:int, cortes: int, volume: int, tipo='SPOT',STAGE='prod'):
    """
        Função criada para possibilitar o envio de decks para a prospec-true através do lambda enviarZipsDecks
    """
    
    BUCKET_MODELOS_TRUE = f'true-modelos-preco-{STAGE}'
    try: configs = json.loads(utils_s3.get_obj_from_s3(BUCKET_MODELOS_TRUE,'configuracoes/configs.json'))
    except: configs = {}
    RegiaoStackTrueModelosPreco = configs.get('REGIAO_STACK',"us-east-1")
    print(f"REGIÃO STACK TRUE MODELOS PREÇO: {RegiaoStackTrueModelosPreco}")
    lambda_function_US = boto3.client('lambda',region_name = RegiaoStackTrueModelosPreco)

    # if modo_execucao == 2:
    #     maquina_nw = "4X"
    #     maquina_dc = "2X" 
    # else:
    #     maquina_nw = "16X"
    #     maquina_dc = "4X"

    payload = {
        "TIPO": tipo,
        # "MAQUINA_DC": maquina_dc,
        # "MAQUINA_NW": maquina_nw,
        "CORTES": cortes,
        "VOLUME": volume,
        "TITULO": titulo,
        "TAGS": tags,
        "MAX_TRATAMENTOS": max_inviabilidades,
        "CAMINHO_S3": key_name,
        "BUCKET_S3": bucket_s3,
        "TENTATIVAS": 3,
        "CONSISTENCIA": modo_execucao,
        "USUARIO":"Automático",
    }
    response = lambda_function_US.invoke(FunctionName=f'true-modelos-preco-{STAGE}-enviarZipsDecks', Payload=json.dumps(payload))['Payload'].read().decode()
    return json.loads(response)[0]