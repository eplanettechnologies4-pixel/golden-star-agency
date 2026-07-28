import logging
import requests
from celery import shared_task
from django.conf import settings
import os

logger = logging.getLogger(__name__)


@shared_task
def trigger_n8n_content_update_webhook(post_id):
    """
    Async Celery task triggered when a blog post status becomes 'published'.
    Sends payload to N8N_WEBHOOK_URL + '/content-update'.
    Payload: {"content_type": "blog", "id": post.id, "title": post.title, "slug": post.slug}
    """
    from apps.blog.models import BlogPost

    try:
        post = BlogPost.objects.filter(pk=post_id).first()
        if not post:
            logger.warning(f"[n8n Webhook] BlogPost with ID {post_id} not found.")
            return False

        n8n_base_url = getattr(settings, 'N8N_WEBHOOK_URL', os.environ.get('N8N_WEBHOOK_URL', 'http://localhost:5678/webhook'))
        webhook_url = n8n_base_url.rstrip('/') + '/content-update'

        payload = {
            "content_type": "blog",
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
        }

        logger.info(f"[n8n Webhook] Dispatching payload to {webhook_url}: {payload}")
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.ok:
            logger.info(f"[n8n Webhook ✓] Success response from n8n: {response.status_code}")
            return True
        else:
            logger.error(f"[n8n Webhook ✗] Failed response from n8n ({response.status_code}): {response.text}")
            return False
    except Exception as exc:
        logger.exception(f"[n8n Webhook Exception] Error delivering webhook for BlogPost {post_id}: {exc}")
        return False
