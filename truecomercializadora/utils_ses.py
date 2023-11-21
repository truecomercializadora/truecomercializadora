import boto3
from botocore.exceptions import ClientError

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(sender, recipients_dict, content_dict, attachments = None):
  """
  # ============================================================================================ #
  #  Send a multipart email using the Amazon SES Service.                                        #
  #   - Senders and recipients should be verified using the SES Identity Management              #
  #   - Permission. Client should have IAM Role permission to "ses:SendRawEmail"                 #
  #   - Inputs:                                                                                  #
  #      'sender': String "Test Sender <test@truecomercializadora.com>"                          #
  #      'recipients_dict': dictionary. Where each key has a list of email strings               #
  #        {                                                                                     #
  #          'ToAddresses': ["recipient@truecomercializadora.com"],                              #
  #          'CcAddresses': ["recipient@truecomercializadora.com"],                              #
  #          'BccAddresses': []                                                                  #
  #        }                                                                                     #
  #      'content_dict':  list of dict. Each key has information regarding the email content     #
  #         including email subject, a simple text body and and html body                        #   
  #        {                                                                                     #
  #          'subject': '{} - {}'.format(HEADING, DATA),                                         #
  #          'body_text': '',                                                                    #
  #          'body_html': 'triple quotes'                                                        #
  #             <html>                                                                           #
  #               <head></head>                                                                  #
  #                <body>                                                                        #
  #                <h3>Example Heading</h3>                                                      #
  #                                                                                              #
  #                <p>This is an example of a html body for an email.</p>                        #
  #                                                                                              #
  #                <h4>An example of disclaimer could be placed here</h4>                        #
  #              </body>                                                                         #
  #             </html>                                                                          #
  #        'triple quotes'                                                                       #
  #        }                                                                                     #
  #   'attachment_dict': is and optional dictionary containing the information regarding an      #
  #      attachment. This version allows a single attachment per email, this feature should be   #
  #       updated.                                                                               #
  #       {'file_name': file_name, 'io_content': requests.get(file_url).content}                 #
  #   'public' is an optional boolean to allow the uploaded file to be publicly available.       #
  # ============================================================================================ #
  """

  AWS_REGION = "us-east-1"
  CHARSET = "UTF-8"
  
  SUBJECT = content_dict['subject']
  BODY_TEXT = content_dict['body_text']
  BODY_HTML = content_dict['body_html']

  # Create a new SES resource and specify a region.
  client = boto3.client('sesv2',region_name=AWS_REGION)

  # Create a multipart/mixed parent container.
  msg = MIMEMultipart('mixed')
  msg['Subject'] = SUBJECT 
  msg['From'] = sender 
  msg['To'] = ', '.join(recipients_dict['ToAddresses'])
  msg['Cc'] = ', '.join(recipients_dict['CcAddresses'])
  msg['Bcc'] = ', '.join(recipients_dict['BccAddresses'])

  # Create a multipart/alternative child container.
  msg_body = MIMEMultipart('alternative')

  # Encode the text and HTML content and set the character encoding. This step is
  # necessary if you're sending a message with characters outside the ASCII range.
  textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
  htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

  # Add the text and HTML parts to the child container.
  msg_body.attach(textpart)
  msg_body.attach(htmlpart)
  msg.attach(msg_body)

  # Define the attachment part and encode it using MIMEApplication.
  if attachments != None:
    for attachment_dict in attachments:
      att = MIMEApplication(attachment_dict['io_content'])
      att.add_header('Content-Disposition','attachment',filename=attachment_dict['file_name'])
      msg.attach(att)    
  
  try:
    return client.send_email(
        FromEmailAddress=sender,
        Content={
            'Raw':{'Data':msg.as_string()},
        },
    )
  except ClientError as e:
    return e.response['Error']['Message']