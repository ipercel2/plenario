import boto3
import unittest

from plenario import create_app
from plenario.api import prefix
from plenario.api.jobs import *
from tests.jobs import RANDOM_NAME


class TestJobs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # setup flask app instance
        cls.app = create_app().test_client()

        # setup up sqs queue with a random name (to avoid 60 second deletion cooldown)
        cls.client = boto3.client('sqs')
        cls.queue_name = RANDOM_NAME
        cls.queue = cls.client.create_queue(
            QueueName=cls.queue_name,
            Attributes={'VisibilityTimeout': '0'}
        )

        mock_messages = [
            {'Id': '1', 'MessageBody': 'TestMessage!'},
            {'Id': '2', 'MessageBody': 'Space Dandy!'},
            {'Id': '3', 'MessageBody': 'Yeah baby!'},
            {'Id': '4', 'MessageBody': 'You can do it!'},
            {'Id': '5', 'MessageBody': 'Why!'}
        ]

        # seed queue with mock data
        cls.response = cls.client.send_message_batch(
            QueueUrl=cls.queue['QueueUrl'],
            Entries=mock_messages
        )

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
        response = self.app.post(prefix + '/jobs?datatype=timeseries&obs_date__ge=2016-1-1')
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

        msg_id = enqueue_message(RANDOM_NAME, 'Hello!')
        self.assertIsNotNone(msg_id)

    @classmethod
    def tearDownClass(cls):

        # clean up test environment
        cls.client.delete_queue(QueueUrl=cls.queue['QueueUrl'])
