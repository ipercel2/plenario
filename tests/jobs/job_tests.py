import boto3
import unittest

from plenario import create_app
from plenario.api.jobs import *
from tests.jobs import RANDOM_QUEUE_NAME


class TestJobs(unittest.TestCase):

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

    # =====================
    # TEST: enqueue_message
    # =====================

    def test_enqueue_message_good_params(self):

        msg_id = enqueue_message(RANDOM_QUEUE_NAME, 'Hello!')
        self.assertIsNotNone(msg_id)


    @classmethod
    def tearDownClass(cls):

        # clean up test environment
        cls.client.delete_queue(QueueUrl=cls.queue['QueueUrl'])
