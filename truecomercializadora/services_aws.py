import boto3
import io
import logging
import operator
import pandas as pd
import re
import time

from . import utils_types

AVAILABLE_REGIONS = [
    "us-eas-1",
    "us-west-2",
    "us-west-1",
    "eu-west-1",
    "eu-central-1",
    "ap-southeast-1",
    "ap-northeast-1",
    "ap-southeast-2",
    "ap-northeast-2",
    "sa-east-1",
    "cn-north-1",
    "ap-south-1"
]

PROTECTED_LAKE_KEYS = ['landing', 'staging', 'consume']

class Athena:
    '''
    Class encapsulating useful methods associated with the AWS Athena service.
    '''
    
    def __init__(self, region: str, debug: bool=False):
        session = boto3.Session()

        # Public Attributes
        self.region = region
        
        # Private Attributes
        self._athenaClient = session.client('athena', region_name=region)
        self._s3Client = session.client('s3')
        self._s3Resource = session.resource('s3')

        # Initialize logger if debug=True
        self.debug = debug
            

    # Setting the class properties
    region = property(operator.attrgetter('_region'))
    debug = property(operator.attrgetter('_debug'))
        
    @region.setter
    def region(self, r):
        if not r: raise Exception("AWS region cannot be empty")
        if r not in AVAILABLE_REGIONS: raise Exception("AWS region '{r}' does not exist".format(r=r))
        self._region = r

    @debug.setter
    def debug(self, d):
        if type(d) != bool: raise Exception("Debug should be a boolean flag")
        self._debug = d

    # ============================ PRIVATE METHODS =============================
    def __format_query(self, query: str):
        '''
        Returns a string remove any line breaks that might exist if the query was
          writen using triple quotes.
        '''
        return ' '.join([line.strip() for line in query.splitlines()]).strip()

    def __execute_query(self, database: str, query: str, bucket: str, temp_dir: str):
        '''
        Starts the execution of a query on top of a database, and returns the Athena
         query execution object.
        '''
        return self._athenaClient.start_query_execution(
            QueryString=self.__format_query(query=query),
            QueryExecutionContext={'Database': database},
            ResultConfiguration={
                'OutputLocation': "s3://{output_bucket}/{output_folder}".format(
                    output_bucket=bucket,
                    output_folder=temp_dir)
                }
            )

    def __await_query_result(self, executionId: str, timeout: int):
        '''
        Await for the query to finish execution and returns the filename of the
          query result. 
        '''

        state = 'RUNNING'
        
        if self.debug:
            print("Query execution countdown: {timeout}s.".format(timeout=timeout))
        
        while (timeout > 0 and state in ['RUNNING', 'QUEUED']):
            if self.debug:
                print("Query execution countdown: {timeout}s.".format(timeout=timeout))
        
            timeout = timeout - 1
            response = self._athenaClient.get_query_execution(QueryExecutionId = executionId)

            if 'QueryExecution' in response \
                and 'Status' in response['QueryExecution'] \
                and 'State' in response['QueryExecution']['Status']: 

                state = response['QueryExecution']['Status']['State']

                if state == 'FAILED':
                    raise Exception('Query {executionId} failed execution'.format(executionId=executionId))
                elif state == 'SUCCEEDED':
                    s3_path = response['QueryExecution']['ResultConfiguration']['OutputLocation']
                    filename = re.findall(r'.*\/(.*)', s3_path)[0]
                    return filename
            # AWAIT ANOTHER SECOND
            time.sleep(1)

        raise Exception('Query {executionId} timeout after {timeout}s.'.format(
                        executionId=executionId,
                        timeout=timeout))

    def __get_query_result(self, bucket: str, temp_dir: str, query_result_file: str):
        '''
        Returns a pandas DataFrame from the query result file.
        '''
        obj = self._s3Client.get_object(
            Bucket=bucket,
            Key="{temp_dir}/{file_name}".format(
                temp_dir=temp_dir,
                file_name=query_result_file))
        
        return pd.read_csv(io.BytesIO(obj['Body'].read()))

    def __cleanup(self, bucket: str, temp_dir: str):
        '''
        Void method to delete the temporary query result file. 
        '''
        my_bucket = self._s3Resource.Bucket(bucket)

        for item in my_bucket.objects.filter(Prefix=temp_dir):
            item.delete()


    # ============================ PUBLIC METHODS ==============================    
    @utils_types.type_check
    def query(self, database:str, query: str, timeout:int, bucket: str, temp_dir: str):
        '''
        Returns a pandas dataframe out of query.
          database: Database defined in Athena
          query: SQL query to be executed on the database
          timeout: Timeout to wait for execution (seconds)
          bucket: Bucket where the file resulting from the query shall be writen
          temp_dir: Temporary directory inside the bucket where the file will stay
            until the dataset is processed and returned.

        Once the dataframe is produced, the query file gets deleted.
        '''

        # Check if temporary repository has one of the protected keys
        if temp_dir in PROTECTED_LAKE_KEYS:
            raise Exception('Temporary dir {temp_dir} has protected keyword')
        
        # Execute SQL Query
        execution = self.__execute_query(
            database=database,
            query=query,
            bucket=bucket,
            temp_dir=temp_dir)

        # Await for results
        query_result_file = self.__await_query_result(
            executionId=execution['QueryExecutionId'],
            timeout=timeout)

        # Get a dataset out of the result
        dataset = self.__get_query_result(
            bucket=bucket,
            temp_dir=temp_dir,
            query_result_file=query_result_file)

        # Cleanup temporary directory
        self.__cleanup(bucket=bucket, temp_dir=temp_dir)

        return dataset