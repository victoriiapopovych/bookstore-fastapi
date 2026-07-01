import asyncio

from celery.signals import worker_process_init, worker_process_shutdown

from app.db.mongodb import connect_to_mongo, close_mongo_connection


@worker_process_init.connect
def init_worker(**kwargs):
    asyncio.run(connect_to_mongo())


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    asyncio.run(close_mongo_connection())