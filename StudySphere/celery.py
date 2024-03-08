from __future__ import absolute_import

import os
import time

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'StudySphere.settings')
app = Celery('StudySphere')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()