import boto3
import unittest

from plenario import create_app
from plenario.api import prefix
from plenario.api.jobs import *
from plenario.update import create_worker
from tests.jobs import RANDOM_NAME


class TestJobs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # setup flask app instance
        cls.app = create_app().test_client()
        # setup flask app instance for worker
        cls.worker = create_worker().test_client()

        # setup up sqs queue with a random name (to avoid 60 second deletion cooldown)
        cls.client = boto3.client('sqs')
        cls.queue_name = RANDOM_NAME
        cls.queue = cls.client.create_queue(
            QueueName=cls.queue_name,
            Attributes={'VisibilityTimeout': '0'}
        )
        cls.queue_url = cls.queue['QueueUrl']

    # =============
    # TEST: get_job
    # =============

    def test_get_job_good_params(self):
        job_id = RANDOM_NAME + '-get_job_test_1'

        submit_job_record('/test/', job_id)
        response = self.app.get(prefix + '/jobs/' + job_id)
        self.assertEqual(response.status, '200 OK')

    def test_get_job_bad_id(self):
        job_id = RANDOM_NAME + '-get_job_test_2'

        submit_job_record('/test/', job_id)
        response = self.app.get(prefix + '/jobs/' + 'not_an_id')
        self.assertEqual(response.status, '500 INTERNAL SERVER ERROR')

    # ==============
    # TEST: post_job
    # ==============

    def test_post_job_good_params(self):
        response = self.app.get(prefix + '/jobs?datatype=timeseries&obs_date__ge=2016-1-1')
        self.assertEqual(response.status, '200 OK')

    # =======================
    # TEST: submit_job_record
    # =======================

    def test_submit_job_record_good_params(self):
        # +1 because of the other record created with RANDOM_NAME
        # I don't like this... ^
        result = submit_job_record('/test/', RANDOM_NAME + '-42')
        self.assertIsNotNone(result)

    # =====================
    # TEST: enqueue_message
    # =====================

    def test_enqueue_message_good_params(self):

        enqueue_message(RANDOM_NAME, 'Hello!')
        receipt_handle = self.client.receive_message(QueueUrl=self.queue_url)['Messages'][0]['ReceiptHandle']
        self.assertIsNotNone(receipt_handle)
        self.client.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)

    # =====================
    # TEST: Worker Endpoint
    # =====================

    def test_worker_endpoint_execute_job(self):
        """Establish that the worker has successfuly recieved the job, executed it,
        and updated the appropriate record. Do this with a dummy job that wasn't fetched
        from the queue."""

        job_id = RANDOM_NAME + '-worker_test_1'

        submit_job_record('/test_url/', job_id)
        self.worker.post('/job', data={'title': job_id, 'text': 'do_this_for_me'})

        job = Session.query(JobRecord).filter(JobRecord.id == job_id).first()

        self.assertIsNotNone(job.result)

    def test_worker_endpoint_execute_with_job_from_queue(self):
        """Establish that worker has done everything stated in the previous method,
        but this time with a message that's made it through the queue."""

        job_id = enqueue_message(RANDOM_NAME, 'detail_aggregate?dataset_name=flu_shot_clinics&obs_date__ge=2016-1-1')
        submit_job_record('/jobs/', job_id)

        message = self.client.receive_message(QueueUrl=self.queue['QueueUrl'])['Messages'][0]

        self.worker.get('/jobs/' + message['MessageId'] + '/' + message['Body'])

        job = Session.query(JobRecord).filter(JobRecord.id == job_id).first()

        self.assertIsNotNone(job.result)

    # =======================
    # TEST: jobable decorator
    # =======================

    def test_jobable_on_detail_aggregate(self):
        """Establish that the jobbable decorator queued the appropriate message and
        corresponding database JobRecord."""

        # issue a request, exactly as a user would, to the timeseries endpoint
        self.app.get('/v1/api/timeseries?dataset_name=flu_shot_clinics&obs_date__ge=2016-1-1&job=true')

        # retrieve queued message and job record
        message = self.client.receive_message(QueueUrl=self.queue['QueueUrl'])['Messages'][0]
        job = Session.query(JobRecord).filter(JobRecord.id == message['MessageId']).first()

        # stand in for EB, and send the job to Worker
        self.worker.get('/jobs/' + message['MessageId'] + '/' + message['Body'])

        # assert that both the message and job exist, and that they are the same
        self.assertIsNotNone(message)
        self.assertIsNotNone(job)
        self.assertEquals(job.id, message['MessageId'])

        # assert that the job returned with a successful result
        self.assertIsNotNone(job.result)

        # now check on your job!
        response = self.app.get(job.url)

    @classmethod
    def tearDownClass(cls):

        # clean up test environment
        cls.client.delete_queue(QueueUrl=cls.queue_url)
