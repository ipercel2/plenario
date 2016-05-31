"""jobs: api endpoint for submitting, monitoring, and deleting jobs"""

# api => flask blueprint instance
# prefix => namespacing string '/v1/api'
from . import api, prefix

# HTTP      URI         ACTION
# ============================
# GET       /jobs/:id   retrieve job status
# POST      /jobs       submit new job
# DELETE    /jobs/:id   cancel ongoing job


@api.route(prefix + '/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    # TODO: check job queue for job_id
    # status = SQS.check(job_id)
    if 'status' == 'completed':
        return '200 OK: Job Results for:', job_id
    elif 'status' == 'in_progress':
        # TODO: Status template?
        return '200 Ok: job status for:', job_id
    else:
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
