"""jobs: api endpoint for submitting, monitoring, and deleting jobs"""

import boto3

from plenario.api import api, prefix
from plenario.database import session
from plenario.models import JobRecord
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

    _session = session()

    try:
        rp = _session.query(JobRecord).filter(JobRecord.id == job_id)
        job_status = rp.first()

        return '200 OK: Job Results for:' + job_id +
    except LookupError as err:
        return '404 Not found: bad request for:', job_id


@api.route(prefix + '/jobs', methods=['POST'])
def post_job():
    return '202 Accepted: here is your job location'


@api.route(prefix + '/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    return '200 Ok: job', job_id, 'removed'


# ===========
# Job Methods
# ===========

def jobable(func):
    """
    Decorating for existing route functions. Allows user to specify if they
    would like to add their query to the job queue and recieve a ticket.

    :param func: api endpoint

    :returns: decorated endpoint
    """

    def decorated(is_job=False, *args, **kwargs):

        if is_job:

            # TODO: What's message going to be? How do we get it? How does the worker interpret it?
            job_id = enqueue_message(RANDOM_QUEUE_NAME, message)
            base_url = prefix + '/jobs/' + job_id

            _session = session()

            # commit the job record, be loud if anything goes wrong
            try:
                job_rec = submit_job_record(base_url, job_id, _session)
                _session.commit()
            except:
                _session.rollback()
                raise Exception('(jobable) session failed to commit job record')
            finally:
                _session.close()

            # TODO: replace with something nicer please
            return "Find your job at: " + job_rec.url

        else:
            return func(args)

    return decorated


def submit_job_record(base_url, job_id, session):
    """
    Create a job record in the database that keeps track of a job's status.

    :param base_url: the whole url EXCEPT the job_id
    :param job_id: the message id returned from when job was enqueued
    :param session: a dependancy, to keep the function independant of the
                    context it's run inn

    :return: a copy of the record object
    """

    job_rec = JobRecord(id=job_id, status='ongoing', url=base_url + job_id)
    session.add(job_rec)
    return job_rec


# ===========
# SQS Methods
# ===========

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

