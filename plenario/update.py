import json
import plenario.tasks as tasks

from flask import Flask, abort, request
from multiprocessing import Process

from plenario.api import detail_aggregate
from plenario.database import session as Session
from plenario.models import JobRecord
from plenario.tasks import celery_app


"""
Task server that runs in AWS Elastic Beanstalk worker environment.
Takes POST requests for cron-scheduled tasks.
Posts most of them to the Celery queue living on Redis,
but also runs METAR updates right away.
"""


def create_worker():
    app = Flask(__name__)
    app.config.from_object('plenario.settings')
    app.url_map.strict_slashes = False

    @app.route('/update/weather', methods=['POST'])
    def weather():
        tasks.update_weather.delay()
        return "Sent off weather task"

    @app.route('/update/<frequency>', methods=['POST'])
    def update(frequency):
        try:
            dispatch[frequency]()
            return "Sent update request"
        except KeyError:
            abort(400)

    @app.route('/health')
    def check_health():
        if celery_app.control.ping():
            return "Someone is listening."
        else:
            abort(503)

    @app.route('/jobs/<job_id>/<job_method>', methods=['GET'])
    def execute_job(job_id, job_method):
        # get corresponding job
        job = Session.query(JobRecord).filter(JobRecord.id == job_id).first()
        # update status for the user
        job.status = 'ongoing'
        # json result of running specified query
        result = execute(job_method, request.args)
        # final update on the job record and store results
        job.status = 'completed'
        job.result = json.dumps(result.data)
        Session.commit()

        return "Job ID: " + job.id + " completed."

    return app


# TODO: Find somewhere else to put this.
def execute(job_method, job_args):
    """
    Parse string and decide what methods need to be executed on the backend.

    :param : string containing job query specifics

    :returns: query result in json format
    """

    methods = {
        'detail_aggregate': detail_aggregate
    }

    return methods[job_method](job_args)


def often_update():
    # Keep METAR updates out of the queue
    # so that they run right away even when the ETL is chugging through
    # a big backlog of event dataset updates.

    # Run METAR update in new thread
    # so we can return right away to indicate the request was received
    Process(target=tasks.update_metar).start()


def daily_update():
    tasks.update_weather.delay()
    tasks.frequency_update.delay('daily')


def weekly_update():
    tasks.frequency_update.delay('weekly')


def monthly_update():
    tasks.frequency_update.delay('monthly')


def yearly_update():
    tasks.frequency_update.delay('yearly')

dispatch = {
    'often': often_update,
    'daily': daily_update,
    'weekly': weekly_update,
    'monthly': monthly_update,
    'yearly': yearly_update
}
