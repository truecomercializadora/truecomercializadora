import boto3
from botocore.exceptions import ClientError
import io
import logging

def _get_s3_client():
    """
    # ============================================================================================ #
    #  Build an S3 client. Make sure you have proper credentials installed in your machine         #
    #   which can be done using the aws cli:                                                       #
    #    https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html                  #
    # ============================================================================================ #
    """

    return boto3.client('s3')


def _remove_access_key_from_link(url):
    """
    # ============================================================================================ #
    #  Remove the access key information from a generated url                                      #
    # ============================================================================================ #
    """
    url=url.split('?')[0]
    return url


def get_obj_from_s3(bucket_name, key_name):
    """
    # ============================================================================================ #
    #  Return an object from s3 based on its bucket and keyname as long as the client has access   #
    #   to it.                                                                                     #
    # ============================================================================================ #
    """

    client = _get_s3_client()
    return client.get_object(Bucket = bucket_name, Key = key_name)['Body'].read()


def list_s3_files(bucket_name, prefix):
    """
    # ============================================================================================ #
    #  Return an iterable of files within a S3 bucket based on a prefix. A prefix could be a fol-  #
    #   der within S3.                                                                             #
    # ============================================================================================ #
    """

    client = _get_s3_client()
    response = client.list_objects(Bucket = bucket_name, Prefix = prefix)
    for content in response.get('Contents', []):
        yield content.get('Key')

def list_all_s3_files(bucket_name,prefix=None,region_name='sa-east-1'):
    """ 
    # ============================================================================================ #
    # Funcao para retornar todo o conteudo de uma determinada pasta. Seu retorno eh um PageItera-  #
    # tor que ao ser utilizado com o loop for possui os dicionarios com todos os parametros dos    #
    # arquivos localizados na pasta.Seu conteudo principal pode ser acessado em page['Contents']   # 
    # ============================================================================================ #
    """
    client = boto3.client('s3', region_name=region_name)
    paginator = client.get_paginator('list_objects')
    if prefix != None:
        page_iterator = paginator.paginate(Bucket=bucket_name,Prefix = prefix)
    else:
        page_iterator = paginator.paginate(Bucket=bucket_name)

    return page_iterator



def upload_io_object(dataIO, bucket_name, key_name, public=False):
    """
    # ============================================================================================ #
    #  Upload a file to S3 from an IO of bytes. Make sure the dataIO is of type _io.BytesIO.       #
    #   Client should have access to the S3 bucket with IAM policy allowing:                       #
    #      - s3:PutObject                                                                          #
    #      - s3:PutObjectAcl                                                                       #
    #   'bucket_name' is a string representing the bucket name where the file should be placed.    #
    #   'key_name' is a string representing the file name and its path related to the bucket:      #
    #       'test/test.csv'                                                                        #
    #   'public' is an optional boolean to allow the uploaded file to be publicly available.       #
    # ============================================================================================ #
    """
    if type(dataIO) != io.BytesIO:
        raise Exception("'upload_io_object' can only receive an io.BytesIO as file content")

    client = _get_s3_client()
    if public:
        extra_args =  {'ACL': 'public-read'}
    else:
        extra_args = None

    client.upload_fileobj(
        dataIO,
        bucket_name,
        Key = key_name,
        ExtraArgs = extra_args
    )
    url_output = client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket_name,
            'Key': key_name
        }
    )
    return _remove_access_key_from_link(url_output)

def create_presigned_url(client_method_name:str, method_parameters: str=None,
                                  expiration: int=3600, http_method: str=None) -> str:
    """Generate a presigned URL to invoke an S3.Client method

    Not all the client methods provided in the AWS Python SDK are supported.

    :param client_method_name: Name of the S3.Client method, e.g., 'list_buckets'
    :param method_parameters: Dictionary of parameters to send to the method
    :param expiration: Time in seconds for the presigned URL to remain valid
    :param http_method: HTTP method to use (GET, etc.)
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 client method
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url(ClientMethod=client_method_name,
                                                    Params=method_parameters,
                                                    ExpiresIn=expiration,
                                                    HttpMethod=http_method)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

def check_prefix_has_contents(Bucket: str, Prefix: str) -> bool:
    '''
    Returns True if prefix has contents in it or False if it
     does not
    '''
    
    client = _get_s3_client()
    try:
        response = client.list_objects(
            Bucket = Bucket,
            Prefix = Prefix)

        if response.get('Contents'):
            return True
        else:
            return False
    except ClientError as e:
        raise e