"""Celery Beat schedule configuration."""

from celery.schedules import crontab
from app.config import settings

# Celery Beat schedule
beat_schedule = {
    # Poll station status every 30 seconds
    'poll-station-status': {
        'task': 'poll_station_status',
        'schedule': settings.GBFS_POLL_INTERVAL_REALTIME,
        'options': {'queue': 'realtime'}
    },
    # Poll free bike status every 30 seconds
    'poll-free-bike-status': {
        'task': 'poll_free_bike_status',
        'schedule': settings.GBFS_POLL_INTERVAL_REALTIME,
        'options': {'queue': 'realtime'}
    },
    # Poll station information every 12 hours
    'poll-station-information': {
        'task': 'poll_station_information',
        'schedule': settings.GBFS_POLL_INTERVAL_STATIC,
        'options': {'queue': 'static'}
    },
}

# Task routing
task_routes = {
    'poll_station_status': {'queue': 'realtime'},
    'poll_free_bike_status': {'queue': 'realtime'},
    'poll_station_information': {'queue': 'static'},
}