import boto3
import json
import os

def publish_message(message, TOPIC_ARN):
  """
  # ============================================================================================ #
  # Publish a message to a SNS TOPIC. Make sure you have proper credentials installed in your    #
  #   machine which can be done using the aws cli:                                               #
  #    https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html                  #
  # 'message' should of type (list, dict or str) and 'TOPIC_ARN'  should be a string representing#
  #   the TOPIC ARN to which the message should be published.                                    #
  # ============================================================================================ #
  """
  sns_client = boto3.client('sns')
  return sns_client.publish(
    TopicArn = TOPIC_ARN,
    Message = json.dumps(message)
  )