from __future__ import annotations

from functools import lru_cache

from shared.config.settings import get_settings


@lru_cache
def get_celery_app():
    """Lazy import: celery is only in the 'worker' extra. broker_url/result_backend read
    from Redis settings; apps/worker/worker.py imports this app and registers tasks
    from apps/worker/tasks.py."""
    from celery import Celery

    url = getattr(get_settings(), "redis_url", "redis://localhost:6379/0")
    app = Celery("rag_os", broker=url, backend=url)
    app.conf.task_serializer = "json"
    app.conf.result_serializer = "json"
    app.conf.accept_content = ["json"]
    return app
