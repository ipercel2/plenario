"""jobs: api endpoint for submitting, monitoring, and deleting jobs"""

import boto3

from plenario.database import session as Session
from plenario.models import JobRecord
from flask import request
from functools32 import wraps
from tests.jobs import RANDOM_NAME

# for testing only, difficult to see if working unless
# hooked up to a real queue. So I have it pointing
# to the temporary queue made by the test suite
MOCK_QUEUE = RANDOM_NAME


# ========================================= #
# HTTP      URI         ACTION              #
# ========================================= #
# GET       /jobs/:id   retrieve job status #
# POST      /jobs       submit new job form #
# DELETE    /jobs/:id   cancel ongoing job  #
# ========================================= #

def get_job(job_id):

    rp = Session.query(JobRecord).filter(JobRecord.id == job_id)
    job = rp.first()
    return '200 OK: Job Results for:' + job.id + ':' + job.status


def post_job():

    # TODO: Establish a friendly form!
    query = request.full_path.split('?')[1]
    job_id = enqueue_message(MOCK_QUEUE, query)
    job_rec = submit_job_record('/v1/api/' + '/jobs/', job_id)
    return "Find your job at: " + job_rec.url


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
        is_job = request.args.get('job')
        query = request.full_path.split('?')[1]
        if is_job:
            job_id = enqueue_message(MOCK_QUEUE, query)
            job_rec = submit_job_record('/v1/api/jobs/', job_id)
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
        job_rec = JobRecord(id=job_id, status='queued', url=base_url + job_id)
        session.add(job_rec)
        session.commit()
        return job_rec
    except Exception as ex:
        session.rollback()
        raise Exception(' submit_job_record :: could not create job record for ' + job_id + '\n\n' + str(ex))
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
