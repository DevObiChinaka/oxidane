"""
Telegram Webhook Handler for Join Requests

This view receives updates from Telegram when users request to join groups.
It automatically approves requests for verified, paid users.

Setup:
1. Set webhook URL: https://yourdomain.com/api/telegram/webhook/
2. Telegram will POST updates here when join requests occur
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from subscriptions.models import TelegramConfiguration
from subscriptions.tasks import approve_telegram_join_request

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """
    Handle incoming Telegram webhook updates
    
    Telegram sends updates for various events. We're interested in:
    - chat_join_request: When a user requests to join a group
    
    Auto-approve if user has active subscription
    """
    try:
        # Parse incoming data
        data = json.loads(request.body)
        
        logger.info(f"Received Telegram webhook update: {json.dumps(data, indent=2)}")
        
        # Handle /verify command
        if 'message' in data and 'text' in data['message']:
            message = data['message']
            text = message['text'].strip()
            
            # Check if it's a /verify command
            if text.startswith('/verify'):
                user = message['from']
                user_id = str(user['id'])
                username = user.get('username', '')
                
                # Extract verification code
                parts = text.split()
                if len(parts) < 2:
                    # No code provided - send help message
                    return JsonResponse({
                        'success': True,
                        'message': 'Please provide verification code: /verify YOUR-CODE'
                    })
                
                verification_code = parts[1].upper().strip()
                
                logger.info(f"Verify command from @{username} (ID: {user_id}), code: {verification_code}")
                
                # Call the verification callback endpoint
                from subscriptions.billing_views import telegram_verify_callback
                from django.test import RequestFactory
                
                factory = RequestFactory()
                verify_request = factory.post(
                    '/api/billing/telegram/verify-callback/',
                    data=json.dumps({
                        'verification_code': verification_code,
                        'telegram_user_id': user_id,
                        'telegram_username': username
                    }),
                    content_type='application/json'
                )
                
                # Add bot secret header
                from django.conf import settings
                verify_request.META['HTTP_X_BOT_SECRET'] = settings.TELEGRAM_BOT_SECRET
                
                # Call verification
                response = telegram_verify_callback(verify_request)
                response_data = json.loads(response.content)
                
                # Send response message to user via Telegram API
                config = TelegramConfiguration.get_instance()
                if config.has_valid_token():
                    import requests as req
                    bot_token = config.decrypt_field('bot_token')
                    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    
                    if response_data.get('success'):
                        message_text = f"✅ Verification successful! Your Telegram account is now linked."
                    else:
                        error_msg = response_data.get('error', 'Unknown error')
                        message_text = f"❌ Verification failed: {error_msg}"
                    
                    req.post(send_url, json={
                        'chat_id': user_id,
                        'text': message_text
                    })
                
                return JsonResponse({
                    'success': True,
                    'message': 'Verification processed'
                })
        
        # Handle chat join request
        if 'chat_join_request' in data:
            join_request = data['chat_join_request']
            
            chat_id = join_request['chat']['id']
            user = join_request['from']
            user_id = user['id']
            username = user.get('username', 'Unknown')
            
            logger.info(f"Join request from @{username} (ID: {user_id}) for chat {chat_id}")
            
            # Trigger auto-approval task asynchronously
            approve_telegram_join_request.delay(chat_id, user_id)
            
            return JsonResponse({
                'success': True,
                'message': 'Join request received, processing approval'
            })
        
        # Other update types (message, callback_query, etc.)
        else:
            logger.debug(f"Unhandled update type: {list(data.keys())}")
            return JsonResponse({'success': True, 'message': 'Update received'})
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook request")
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def set_telegram_webhook(request):
    """
    Set the Telegram webhook URL
    
    Call this endpoint to register your webhook with Telegram.
    POST /api/telegram/set-webhook/
    
    Body: {
        "webhook_url": "https://yourdomain.com/api/telegram/webhook/"
    }
    """
    try:
        data = json.loads(request.body)
        webhook_url = data.get('webhook_url')
        
        if not webhook_url:
            return JsonResponse({
                'success': False,
                'error': 'webhook_url is required'
            }, status=400)
        
        # Get bot token
        config = TelegramConfiguration.get_instance()
        if not config.has_valid_token():
            return JsonResponse({
                'success': False,
                'error': 'Telegram bot token not configured'
            }, status=400)
        
        bot_token = config.decrypt_field('bot_token')
        
        # Set webhook
        import requests as req
        url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        payload = {
            'url': webhook_url,
            'allowed_updates': ['chat_join_request', 'message', 'callback_query']
        }
        
        response = req.post(url, json=payload, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"Telegram webhook set to: {webhook_url}")
            return JsonResponse({
                'success': True,
                'message': f'Webhook set successfully to {webhook_url}',
                'result': result
            })
        else:
            error = result.get('description', 'Unknown error')
            logger.error(f"Failed to set webhook: {error}")
            return JsonResponse({
                'success': False,
                'error': error
            }, status=400)
    
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def get_webhook_info(request):
    """
    Get current webhook information from Telegram
    
    GET /api/telegram/webhook-info/
    """
    try:
        config = TelegramConfiguration.get_instance()
        if not config.has_valid_token():
            return JsonResponse({
                'success': False,
                'error': 'Telegram bot token not configured'
            }, status=400)
        
        bot_token = config.decrypt_field('bot_token')
        
        # Get webhook info
        import requests as req
        url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        
        response = req.get(url, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            return JsonResponse({
                'success': True,
                'webhook_info': result['result']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('description', 'Unknown error')
            }, status=400)
    
    except Exception as e:
        logger.error(f"Error getting webhook info: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
