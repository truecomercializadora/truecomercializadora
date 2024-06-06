import boto3
from botocore.exceptions import ClientError
import io
import logging

def _get_db_resource(region_name):
    """
    # ============================================================================================ #
    #  Build an dynamo resource. Make sure you have proper credentials installed in your machine   #
    #   which can be done using the aws cli:                                                       #
    #    https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html                  #
    # ============================================================================================ #
    """
    return boto3.resource('dynamodb',region_name=region_name)

def get_planilha(servico, aba,stage,region_name='sa-east-1'):
    """
    # ============================================================================================ #
    # retorna o atributo dados da planilha true que consta no dynamodb                             #
    # ============================================================================================ #
    """
    dynamodb = _get_db_resource(region_name)
    table = dynamodb.Table(f'planilhas-true-{stage}')
    response = table.get_item(Key={'servico': servico,'aba': aba})
    if 'Item' in response.keys():
        return response['Item']['dados']
    else:
        raise Exception(f"'({servico},{aba})' item not found")
    