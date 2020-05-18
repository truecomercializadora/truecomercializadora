import boto3
import io

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