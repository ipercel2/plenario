"""jobs: api endpoint for submitting, monitoring, and deleting jobs"""

import boto3

from plenario.api import api, prefix
from tests.jobs import RANDOM_QUEUE_NAME

# ========================================= #
# HTTP      URI         ACTION              #
# ========================================= #
# GET       /jobs/:id   retrieve job status #
# POST      /jobs       submit new job      #
# DELETE    /jobs/:id   cancel ongoing job  #
# ========================================= #


@api.route(prefix + '/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    try:
        message = fetch_message_from_queue(RANDOM_QUEUE_NAME, job_id)
        return '200 OK: Job Results for:' + job_id + "::" + message['MessageBody']
    except LookupError as err:
        return '404 Not found: bad request for:', job_id


@api.route(prefix + '/jobs', methods=['POST'])
def post_job():
    return '202 Accepted: here is your job location'


@api.route(prefix + '/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    return '200 Ok: job', job_id, 'removed'


# =============
# Job Decorator
# =============

def jobable(func, is_job=False):
    """
    Decorating for existing route functions. Allows user to specify if they
    would like to add their query to the job queue and recieve a ticket.

    :param func: api endpoint
    :param is_job: whether or not to add to the job queue

    :returns: decorated endpoint
    """

    def decorated():
        if is_job:
            # TODO: add job to queue
            # SQS.add(func, args)
            # TODO: generate job uri
            # response['job_uri'] = '/v1/api/jobs/:id'
            pass
        else:
            # return func(args)
            pass

    return decorated


# ===========
# SQS Methods
# ===========

def fetch_message_from_queue(QueueName, MessageId):
    """
    Find and return the message stored in Amazon SQS for this job ID.

    :param QueueName: name of queue in SQS
    :param MessageId: index of the queue to check

    :returns: message
    """

    # fetch existing queue
    client = boto3.client('sqs')
    queue = client.create_queue(QueueName=QueueName)

    # if queue does not exist, be loud
    if queue is None:
        raise LookupError('fetch_message_from_queue() Queue: ' + QueueName + 'not found!')

    # retrieve messages from queue as a ResultSet
    # TODO: this is consuming the messages
    result = client.receive_message(
        QueueUrl=queue['QueueUrl'],
        AttributeNames=['All'],
        MessageAttributeNames=['job_status'],
        MaxNumberOfMessages=10,
        VisibilityTimeout=0
    )

    # look for message
    for message in result['Messages']:
        if message['MessageId'] == MessageId:
            return message

    # if message not found, be loud
    raise LookupError('fetch_message_from_queue() ID: ' + MessageId + ' not found in the queue!')
