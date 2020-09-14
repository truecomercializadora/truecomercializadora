import boto3

def publish_message(
    QueueUrl: str,
    DelaySeconds: int,
    MessageBody: str) -> dict:
    """
    Publish a message to a SQS QUEUE. Make sure you have proper credentials installed in your
     machine which can be done using the aws cli:
     https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html
     'message' should of type str and QueueUrl should be a string representing
     the QueueUrl to which the message should be published.
    """
    sqs_client = boto3.client('sqs')
    
    return sqs_client.send_message(
        QueueUrl=QueueUrl,
        DelaySeconds=DelaySeconds,
        MessageBody=MessageBody)