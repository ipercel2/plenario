"""jobs: api endpoint for submitting, monitoring, and deleting jobs"""

import boto3

from plenario.api import api, prefix
from plenario.database import session as Session
from plenario.models import JobRecord
from flask import Request
from functools32 import wraps
from tests.jobs import RANDOM_QUEUE_NAME


# ========================================= #
# HTTP      URI         ACTION              #
# ========================================= #
# GET       /jobs/:id   retrieve job status #
# POST      /jobs       submit new job form #
# DELETE    /jobs/:id   cancel ongoing job  #
# ========================================= #

@api.route(prefix + '/jobs/<job_id>', methods=['GET'])
def get_job(job_id):

    try:
        rp = Session.query(JobRecord).filter(JobRecord.id == job_id)
        job_status = rp.first()
        return '200 OK: Job Results for:' + job_id + ':' + job_status
    except LookupError:
        return '404 Not found: bad request for:', job_id


@api.route(prefix + '/jobs', methods=['POST'])
def post_job():

    query = Request.full_path.split('?')[1]
    job_id = enqueue_message(RANDOM_QUEUE_NAME, query)
    job_rec = submit_job_record('/v1/api/' + '/jobs/' + job_id, job_id)
    return "Find your job at: " + job_rec.url


@api.route(prefix + '/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    return '200 Ok: job', job_id, 'removed'


# ===========
# Job Methods
# ===========
# jobable: decorator which is responsible for providing the option to submit jobs
# submit_job_record: creates a record to keep track of a job's status and result
# enqueue_message: creates a job message and adds it to a queue for the worker

def jobable(fn):
    """
    Decorating for existing route functions. Allows user to specify if they
    would like to add their query to the job queue and recieve a ticket.

    :param fn: flask route function

    :returns: decorated endpoint
    """

    @wraps
    def wrapper(*args, **kwargs):
        is_job = Request.args.get('job')
        query = Request.full_path.split('?')[1]
        if is_job:
            job_id = enqueue_message(RANDOM_QUEUE_NAME, query)
            job_rec = submit_job_record('/v1/api/' + '/jobs/' + job_id, job_id)
            # TODO: Replace with a template.
            return "Find your job at: " + job_rec.url
        else:
            return fn(*args, **kwargs)
    return wrapper


def submit_job_record(base_url, job_id):
    """
    Create a job record in the database that keeps track of a job's status.

    :param base_url: the whole url EXCEPT the job_id
    :param job_id: the message id returned from when job was enqueued

    :return: a copy of the record object
    """

    session = Session()
    try:
        job_rec = JobRecord(id=job_id, status='ongoing', url=base_url + job_id)
        session.add(job_rec)
        session.commit()
        return job_rec
    except:
        session.rollback()
        raise Exception('submit_job_record :: could not create job record for ' + job_id)
    finally:
        session.close()


def enqueue_message(queue_name, message):
    """
    Submit job to the Amazon SQS queue. Return MessageId to use as the job ID.

    :param queue_name: name of queue in SQS
    :param message: content to submit

    :returns: ReceiptHandle
    """

    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    return queue.send_message(
        MessageBody=message,
        DelaySeconds=0,
    )['MessageId']
