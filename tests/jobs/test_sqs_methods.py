import boto3
import unittest

from plenario import create_app
from plenario.api import prefix
from plenario.api.jobs import *
from tests.jobs import RANDOM_QUEUE_NAME


class TestSQSMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # setup flask app instance
        cls.app = create_app().test_client()

        # setup up sqs queue with a random name (to avoid 60 second deletion cooldown)
        cls.client = boto3.client('sqs')
        cls.queue_name = RANDOM_QUEUE_NAME
        cls.queue = cls.client.create_queue(
            QueueName=cls.queue_name,
            Attributes={'VisibilityTimeout': '0'})

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

    # ==============================
    # TEST: fetch_message_from_queue
    # ==============================

    def test_fetch_message_from_queue_with_good_input(self):

        target_message_id = self.response['Successful'][0]['MessageId']

        message = fetch_message_from_queue(
            QueueName=self.queue_name,
            MessageId=target_message_id
        )

        self.assertIsNotNone(message)

    def test_fetch_message_bad_queue(self):

        target_message_id = self.response['Successful'][0]['MessageId']

        self.assertRaises(
            LookupError,
            fetch_message_from_queue,
            QueueName='NOTTESTING',
            MessageId=target_message_id
        )

    def test_fetch_message_bad_message(self):

        self.assertRaises(
            LookupError,
            fetch_message_from_queue,
            QueueName=self.queue_name,
            MessageId='o hai ther'
        )

    # =============
    # TEST: get_job
    # =============

    def test_get_job_with_good_input(self):

        target_message_id = self.response['Successful'][0]['MessageId']
        result = self.app.get(prefix + '/jobs/' + target_message_id)
        print result

    @classmethod
    def tearDownClass(cls):

        # clean up test environment
        cls.client.delete_queue(QueueUrl=cls.queue['QueueUrl'])
