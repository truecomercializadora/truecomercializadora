import boto3
import json
import os

def publish_message(
    message: dict,
    TopicArn: str,
    Subject: str=None,
    MessageAttributes: str=None) -> dict:
    """
    Publish a message to a SNS TOPIC. Make sure you have proper credentials installed in your
     machine which can be done using the aws cli:
     https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html
     'message' should of type (list, dict or str) and 'TOPIC_ARN'  should be a string representing
     the TOPIC ARN to which the message should be published.
    """
    sns_client = boto3.client('sns')
    
    if Subject != None and MessageAttributes==None:
        raise Exception("Subject defined but MessageAttributes == None")
    
    if MessageAttributes:
        return sns_client.publish(
            TopicArn = TopicArn,
            Message = json.dumps(message),
            Subject=Subject,
            MessageAttributes=MessageAttributes
        )
    
    return sns_client.publish(
            TopicArn = TopicArn,
            Message = json.dumps(message)
        )