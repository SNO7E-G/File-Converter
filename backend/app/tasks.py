from celery import Celery
from flask import current_app
import os
import requests
from datetime import datetime
import json

from app.models.db import db
from app.models.conversion import Conversion, Webhook
from app.converters.converter_factory import ConverterFactory
from app.utils.file_utils import cleanup_expired_files

# Initialize Celery
celery = Celery('app')

def configure_celery(app):
    """Configure Celery with Flask application"""
    celery.conf.update(
        broker_url=app.config.get('CELERY_BROKER_URL'),
        result_backend=app.config.get('CELERY_RESULT_BACKEND'),
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    return celery

@celery.task(bind=True, name='process_conversion', max_retries=3)
def process_conversion(self, conversion_id, options=None):
    """Process a single conversion in the background"""
    options = options or {}
    
    try:
        # Get the conversion record
        conversion = Conversion.query.get(conversion_id)
        
        if not conversion:
            raise ValueError(f"Conversion {conversion_id} not found")
        
        # Skip if already completed or failed
        if conversion.status in ['completed', 'failed']:
            return {
                'conversion_id': conversion_id,
                'status': conversion.status,
                'message': 'Conversion already processed'
            }
        
        # Update status to processing
        conversion.status = 'processing'
        db.session.commit()
        
        # Get converter instance
        converter = ConverterFactory.get_converter(
            conversion.source_format, 
            conversion.target_format
        )
        
        # Perform the conversion
        success, error = converter.safe_convert(
            conversion.source_file_path,
            conversion.target_file_path,
            options
        )
        
        # Update the conversion record
        if success:
            conversion.status = 'completed'
            conversion.completed_at = datetime.utcnow()
        else:
            conversion.status = 'failed'
            conversion.error_message = error
        
        db.session.commit()
        
        # Trigger webhooks if conversion is complete
        if success and conversion.webhooks:
            for webhook in conversion.webhooks:
                try:
                    send_webhook_notification.delay(webhook.id, conversion.to_dict())
                except Exception as e:
                    # Log webhook error but continue
                    current_app.logger.error(f"Error sending webhook notification: {str(e)}")
        
        return {
            'conversion_id': conversion_id,
            'status': conversion.status,
            'message': 'Conversion completed successfully' if success else 'Conversion failed',
            'error': conversion.error_message
        }
        
    except Exception as e:
        # Handle unexpected errors
        try:
            conversion = Conversion.query.get(conversion_id)
            if conversion:
                conversion.status = 'failed'
                conversion.error_message = str(e)
                db.session.commit()
        except:
            pass
        
        # Retry the task if appropriate
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            'conversion_id': conversion_id,
            'status': 'failed',
            'message': 'Conversion failed with exception',
            'error': str(e)
        }

@celery.task(bind=True, name='process_batch_conversion', max_retries=3)
def process_batch_conversion(self, conversion_ids, options=None):
    """Process multiple conversions in the background"""
    options = options or {}
    results = []
    
    for conversion_id in conversion_ids:
        # Process each conversion
        result = process_conversion.delay(conversion_id, options)
        results.append(result.id)
    
    return {
        'conversion_ids': conversion_ids,
        'task_ids': results,
        'status': 'processing',
        'message': f'Processing {len(conversion_ids)} conversions'
    }

@celery.task(bind=True, name='send_webhook_notification', max_retries=3)
def send_webhook_notification(self, webhook_id, conversion_data=None):
    """Send a webhook notification"""
    try:
        # Get the webhook record
        webhook = Webhook.query.get(webhook_id)
        
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")
        
        # Get conversion data if not provided
        if conversion_data is None:
            conversion = Conversion.query.get(webhook.conversion_id)
            if not conversion:
                raise ValueError(f"Conversion {webhook.conversion_id} not found")
            conversion_data = conversion.to_dict()
        
        # Prepare the payload
        payload = {
            'webhook_id': webhook_id,
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'conversion.completed',
            'data': conversion_data
        }
        
        # Send the webhook notification
        response = requests.post(
            webhook.url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10  # 10 seconds timeout
        )
        
        # Mark webhook as triggered
        webhook.is_triggered = True
        webhook.triggered_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'webhook_id': webhook_id,
            'status': 'sent',
            'status_code': response.status_code,
            'message': 'Webhook notification sent successfully'
        }
        
    except Exception as e:
        # Retry the task if appropriate
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            'webhook_id': webhook_id,
            'status': 'failed',
            'message': 'Webhook notification failed',
            'error': str(e)
        }

@celery.task(name='check_scheduled_conversions')
def check_scheduled_conversions():
    """Check for scheduled conversions that are due to be processed"""
    # Find conversions that are scheduled and due
    now = datetime.utcnow()
    scheduled_conversions = Conversion.query.filter(
        Conversion.status == 'scheduled',
        Conversion.scheduled_at <= now
    ).all()
    
    for conversion in scheduled_conversions:
        # Update status to pending
        conversion.status = 'pending'
        db.session.commit()
        
        # Process the conversion
        process_conversion.delay(conversion.id)
    
    return {
        'status': 'completed',
        'message': f'Checked {len(scheduled_conversions)} scheduled conversions',
        'scheduled_conversions': len(scheduled_conversions)
    }

@celery.task(name='cleanup_expired_files_task')
def cleanup_expired_files_task():
    """Clean up expired files"""
    result = cleanup_expired_files()
    
    return {
        'status': 'completed',
        'message': 'Cleaned up expired files',
        'cleaned_files': result
    }

# Configure periodic tasks
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic tasks"""
    # Check for scheduled conversions every minute
    sender.add_periodic_task(60.0, check_scheduled_conversions.s(), name='check_scheduled_conversions')
    
    # Clean up expired files daily
    sender.add_periodic_task(86400.0, cleanup_expired_files_task.s(), name='cleanup_expired_files') 