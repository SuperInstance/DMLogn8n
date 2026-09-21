#!/usr/bin/env python3
"""
Payment Systems Integration
Connects with Stripe, PayPal, and cryptocurrency payment providers
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import hashlib
import hmac
from .integration_manager import IntegrationStatus

@dataclass
class PaymentMethod:
    type: str  # 'card', 'bank', 'crypto', 'paypal'
    provider: str
    method_id: str
    last_four: str
    expiry_month: Optional[int]
    expiry_year: Optional[int]
    brand: Optional[str]
    is_default: bool
    metadata: Dict[str, Any]

@dataclass
class PaymentTransaction:
    transaction_id: str
    amount: float
    currency: str
    status: str  # 'pending', 'completed', 'failed', 'refunded'
    payment_method: str
    customer_id: str
    description: str
    metadata: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime]

@dataclass
class Subscription:
    subscription_id: str
    customer_id: str
    plan_id: str
    status: str  # 'active', 'canceled', 'past_due', 'unpaid'
    current_period_start: datetime
    current_period_end: datetime
    amount: float
    currency: str
    interval: str  # 'month', 'year'
    metadata: Dict[str, Any]

class PaymentSystemsIntegration:
    """Integration with payment processing systems"""

    def __init__(self, integration_manager):
        self.manager = integration_manager
        self.logger = logging.getLogger(__name__)
        self.config = {}
        self.status = IntegrationStatus.INACTIVE

        # Payment provider clients
        self.stripe_client = None
        self.paypal_client = None
        self.coinbase_client = None

        # Webhook endpoints
        self.webhook_secrets = {}

        # Payment storage (in production, use database)
        self.transactions: Dict[str, PaymentTransaction] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.payment_methods: Dict[str, List[PaymentMethod]] = {}

    async def initialize(self):
        """Initialize the payment systems integration"""
        self.logger.info("Initializing Payment Systems Integration")

        # Initialize Stripe
        await self._initialize_stripe()

        # Initialize PayPal
        await self._initialize_paypal()

        # Initialize Coinbase Commerce
        await self._initialize_coinbase()

        # Load webhook secrets
        await self._load_webhook_secrets()

        self.status = IntegrationStatus.ACTIVE

    async def _initialize_stripe(self):
        """Initialize Stripe integration"""
        try:
            secret_key = self.config.get('api_keys', {}).get('stripe_secret_key')
            if secret_key:
                import stripe
                stripe.api_key = secret_key
                self.stripe_client = stripe
                self.logger.info("Stripe integration initialized")
        except ImportError:
            self.logger.warning("Stripe library not installed")
        except Exception as e:
            self.logger.error(f"Failed to initialize Stripe: {e}")

    async def _initialize_paypal(self):
        """Initialize PayPal integration"""
        try:
            client_id = self.config.get('api_keys', {}).get('paypal_client_id')
            client_secret = self.config.get('api_keys', {}).get('paypal_client_secret')

            if client_id and client_secret:
                self.paypal_client = {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'base_url': 'https://api.paypal.com'  # Use sandbox for testing
                }
                self.logger.info("PayPal integration initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize PayPal: {e}")

    async def _initialize_coinbase(self):
        """Initialize Coinbase Commerce integration"""
        try:
            api_key = self.config.get('api_keys', {}).get('coinbase_api_key')
            if api_key:
                self.coinbase_client = {
                    'api_key': api_key,
                    'base_url': 'https://api.commerce.coinbase.com'
                }
                self.logger.info("Coinbase integration initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Coinbase: {e}")

    async def _load_webhook_secrets(self):
        """Load webhook secrets for verification"""
        self.webhook_secrets = {
            'stripe': self.config.get('api_keys', {}).get('stripe_webhook_secret'),
            'paypal': self.config.get('api_keys', {}).get('paypal_webhook_secret')
        }

    async def create_payment_intent(self, amount: float, currency: str = 'USD',
                                  customer_id: str = None,
                                  payment_method: str = None,
                                  metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a payment intent"""
        try:
            # Use Stripe as default provider
            if self.stripe_client:
                return await self._create_stripe_payment_intent(
                    amount, currency, customer_id, payment_method, metadata or {}
                )
            else:
                return {'success': False, 'error': 'No payment provider available'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _create_stripe_payment_intent(self, amount: float, currency: str,
                                          customer_id: str = None,
                                          payment_method: str = None,
                                          metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create Stripe payment intent"""
        try:
            intent_params = {
                'amount': int(amount * 100),  # Convert to cents
                'currency': currency.lower(),
                'metadata': metadata
            }

            if customer_id:
                intent_params['customer'] = customer_id
            if payment_method:
                intent_params['payment_method'] = payment_method
                intent_params['confirm'] = True

            intent = self.stripe_client.PaymentIntent.create(**intent_params)

            # Store transaction record
            transaction = PaymentTransaction(
                transaction_id=intent.id,
                amount=amount,
                currency=currency,
                status='pending',
                payment_method=payment_method or 'unknown',
                customer_id=customer_id or 'guest',
                description=metadata.get('description', 'Payment'),
                metadata=metadata,
                created_at=datetime.now(),
                completed_at=None
            )
            self.transactions[intent.id] = transaction

            return {
                'success': True,
                'transaction_id': intent.id,
                'client_secret': intent.client_secret,
                'amount': amount,
                'currency': currency,
                'status': intent.status
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def create_paypal_order(self, amount: float, currency: str = 'USD',
                                description: str = '',
                                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create PayPal order"""
        try:
            if not self.paypal_client:
                return {'success': False, 'error': 'PayPal not configured'}

            # Get access token
            token = await self._get_paypal_access_token()
            if not token:
                return {'success': False, 'error': 'Failed to get PayPal access token'}

            # Create order
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            order_data = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'amount': {
                        'currency_code': currency,
                        'value': f"{amount:.2f}"
                    },
                    'description': description
                }]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.paypal_client['base_url']}/v2/checkout/orders",
                    headers=headers,
                    json=order_data
                ) as response:
                    if response.status == 201:
                        order = await response.json()

                        # Store transaction record
                        transaction = PaymentTransaction(
                            transaction_id=order['id'],
                            amount=amount,
                            currency=currency,
                            status='pending',
                            payment_method='paypal',
                            customer_id='guest',
                            description=description,
                            metadata=metadata or {},
                            created_at=datetime.now(),
                            completed_at=None
                        )
                        self.transactions[order['id']] = transaction

                        return {
                            'success': True,
                            'order_id': order['id'],
                            'approval_url': next(link['href'] for link in order['links'] if link['rel'] == 'approve'),
                            'amount': amount,
                            'currency': currency
                        }
                    else:
                        error_text = await response.text()
                        return {'success': False, 'error': f"PayPal error: {error_text}"}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _get_paypal_access_token(self) -> Optional[str]:
        """Get PayPal API access token"""
        try:
            auth = aiohttp.BasicAuth(
                self.paypal_client['client_id'],
                self.paypal_client['client_secret']
            )

            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en_US'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.paypal_client['base_url']}/v1/oauth2/token",
                    auth=auth,
                    headers=headers,
                    data='grant_type=client_credentials'
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['access_token']
                    else:
                        return None
        except Exception as e:
            self.logger.error(f"Error getting PayPal access token: {e}")
            return None

    async def create_crypto_charge(self, amount: float, currency: str = 'USD',
                                 customer_name: str = '',
                                 customer_email: str = '',
                                 metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create cryptocurrency charge via Coinbase Commerce"""
        try:
            if not self.coinbase_client:
                return {'success': False, 'error': 'Coinbase not configured'}

            headers = {
                'X-CC-Api-Key': self.coinbase_client['api_key'],
                'X-CC-Version': '2018-03-22',
                'Content-Type': 'application/json'
            }

            charge_data = {
                'name': metadata.get('description', 'Payment') if metadata else 'Payment',
                'description': metadata.get('description', '') if metadata else '',
                'local_price': {
                    'amount': f"{amount:.2f}",
                    'currency': currency
                },
                'pricing_type': 'fixed_price',
                'metadata': metadata or {}
            }

            if customer_name:
                charge_data['customer_name'] = customer_name
            if customer_email:
                charge_data['customer_email'] = customer_email

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.coinbase_client['base_url']}/charges",
                    headers=headers,
                    json=charge_data
                ) as response:
                    if response.status == 201:
                        charge = await response.json()

                        # Store transaction record
                        transaction = PaymentTransaction(
                            transaction_id=charge['data']['code'],
                            amount=amount,
                            currency=currency,
                            status='pending',
                            payment_method='crypto',
                            customer_id=customer_email or 'guest',
                            description=charge_data['name'],
                            metadata=metadata or {},
                            created_at=datetime.now(),
                            completed_at=None
                        )
                        self.transactions[charge['data']['code']] = transaction

                        return {
                            'success': True,
                            'charge_code': charge['data']['code'],
                            'hosted_url': charge['data']['hosted_url'],
                            'amount': amount,
                            'currency': currency,
                            'expires_at': charge['data']['expires_at']
                        }
                    else:
                        error_text = await response.text()
                        return {'success': False, 'error': f"Coinbase error: {error_text}"}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def capture_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Capture/confirm a payment"""
        try:
            if transaction_id in self.transactions:
                transaction = self.transactions[transaction_id]

                if transaction.payment_method == 'stripe' and self.stripe_client:
                    return await self._capture_stripe_payment(transaction_id)
                elif transaction.payment_method == 'paypal' and self.paypal_client:
                    return await self._capture_paypal_payment(transaction_id)
                else:
                    return {'success': False, 'error': 'Unsupported payment method'}
            else:
                return {'success': False, 'error': 'Transaction not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _capture_stripe_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Capture Stripe payment"""
        try:
            intent = self.stripe_client.PaymentIntent.retrieve(payment_intent_id)

            if intent.status == 'succeeded':
                # Update transaction
                transaction = self.transactions[payment_intent_id]
                transaction.status = 'completed'
                transaction.completed_at = datetime.now()

                # Send webhook event
                await self._send_payment_webhook('payment.completed', transaction)

                return {
                    'success': True,
                    'transaction_id': payment_intent_id,
                    'status': 'completed',
                    'amount': transaction.amount,
                    'currency': transaction.currency
                }
            else:
                return {
                    'success': False,
                    'error': f"Payment not successful: {intent.status}",
                    'status': intent.status
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _capture_paypal_payment(self, order_id: str) -> Dict[str, Any]:
        """Capture PayPal payment"""
        try:
            token = await self._get_paypal_access_token()
            if not token:
                return {'success': False, 'error': 'Failed to get PayPal access token'}

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            async with aiohttp.ClientSession() as session:
                # Capture payment for order
                async with session.post(
                    f"{self.paypal_client['base_url']}/v2/checkout/orders/{order_id}/capture",
                    headers=headers
                ) as response:
                    if response.status == 201:
                        capture_data = await response.json()

                        if capture_data['status'] == 'COMPLETED':
                            # Update transaction
                            transaction = self.transactions[order_id]
                            transaction.status = 'completed'
                            transaction.completed_at = datetime.now()

                            # Send webhook event
                            await self._send_payment_webhook('payment.completed', transaction)

                            return {
                                'success': True,
                                'transaction_id': order_id,
                                'status': 'completed',
                                'amount': transaction.amount,
                                'currency': transaction.currency
                            }
                        else:
                            return {
                                'success': False,
                                'error': f"PayPal capture failed: {capture_data['status']}",
                                'status': capture_data['status']
                            }
                    else:
                        error_text = await response.text()
                        return {'success': False, 'error': f"PayPal capture error: {error_text}"}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def create_subscription(self, customer_id: str, plan_id: str,
                                payment_method: str = None,
                                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a subscription"""
        try:
            if self.stripe_client:
                return await self._create_stripe_subscription(
                    customer_id, plan_id, payment_method, metadata or {}
                )
            else:
                return {'success': False, 'error': 'Subscriptions not supported'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _create_stripe_subscription(self, customer_id: str, plan_id: str,
                                        payment_method: str = None,
                                        metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create Stripe subscription"""
        try:
            subscription_params = {
                'customer': customer_id,
                'items': [{'price': plan_id}],
                'metadata': metadata
            }

            if payment_method:
                subscription_params['default_payment_method'] = payment_method

            subscription = self.stripe_client.Subscription.create(**subscription_params)

            # Store subscription record
            sub_record = Subscription(
                subscription_id=subscription.id,
                customer_id=customer_id,
                plan_id=plan_id,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                amount=subscription['items']['data'][0]['price']['unit_amount'] / 100,
                currency=subscription['items']['data'][0]['price']['currency'],
                interval=subscription['items']['data'][0]['price']['recurring']['interval'],
                metadata=metadata
            )
            self.subscriptions[subscription.id] = sub_record

            return {
                'success': True,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'amount': sub_record.amount,
                'currency': sub_record.currency
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def cancel_subscription(self, subscription_id: str,
                                immediate: bool = False) -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            if subscription_id in self.subscriptions:
                if self.stripe_client:
                    if immediate:
                        self.stripe_client.Subscription.delete(subscription_id)
                    else:
                        self.stripe_client.Subscription.modify(
                            subscription_id,
                            cancel_at_period_end=True
                        )

                    # Update local record
                    subscription = self.subscriptions[subscription_id]
                    subscription.status = 'canceled'

                    return {
                        'success': True,
                        'subscription_id': subscription_id,
                        'status': 'canceled'
                    }
                else:
                    return {'success': False, 'error': 'Subscription provider not available'}
            else:
                return {'success': False, 'error': 'Subscription not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def refund_payment(self, transaction_id: str,
                           amount: float = None,
                           reason: str = '') -> Dict[str, Any]:
        """Refund a payment"""
        try:
            if transaction_id in self.transactions:
                transaction = self.transactions[transaction_id]

                if transaction.payment_method == 'stripe' and self.stripe_client:
                    return await self._refund_stripe_payment(transaction_id, amount, reason)
                elif transaction.payment_method == 'paypal' and self.paypal_client:
                    return await self._refund_paypal_payment(transaction_id, amount, reason)
                else:
                    return {'success': False, 'error': 'Refunds not supported for this payment method'}
            else:
                return {'success': False, 'error': 'Transaction not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _refund_stripe_payment(self, payment_intent_id: str,
                                   amount: float = None,
                                   reason: str = '') -> Dict[str, Any]:
        """Refund Stripe payment"""
        try:
            refund_params = {'payment_intent': payment_intent_id}
            if amount:
                refund_params['amount'] = int(amount * 100)
            if reason:
                refund_params['reason'] = reason

            refund = self.stripe_client.Refund.create(**refund_params)

            # Update transaction status
            transaction = self.transactions[payment_intent_id]
            if refund.status == 'succeeded':
                transaction.status = 'refunded'

            return {
                'success': True,
                'refund_id': refund.id,
                'amount': refund.amount / 100,
                'currency': refund.currency,
                'status': refund.status
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_payment_methods(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get payment methods for a customer"""
        try:
            if customer_id not in self.payment_methods:
                self.payment_methods[customer_id] = []

            return [
                {
                    'method_id': method.method_id,
                    'type': method.type,
                    'provider': method.provider,
                    'last_four': method.last_four,
                    'expiry_month': method.expiry_month,
                    'expiry_year': method.expiry_year,
                    'brand': method.brand,
                    'is_default': method.is_default
                }
                for method in self.payment_methods[customer_id]
            ]

        except Exception as e:
            self.logger.error(f"Error getting payment methods: {e}")
            return []

    async def add_payment_method(self, customer_id: str, method_type: str,
                               provider: str, method_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a payment method for a customer"""
        try:
            if customer_id not in self.payment_methods:
                self.payment_methods[customer_id] = []

            payment_method = PaymentMethod(
                type=method_type,
                provider=provider,
                method_id=method_data.get('method_id', f"{provider}_{len(self.payment_methods[customer_id])}"),
                last_four=method_data.get('last_four', ''),
                expiry_month=method_data.get('expiry_month'),
                expiry_year=method_data.get('expiry_year'),
                brand=method_data.get('brand'),
                is_default=method_data.get('is_default', False),
                metadata=method_data.get('metadata', {})
            )

            self.payment_methods[customer_id].append(payment_method)

            return {
                'success': True,
                'method_id': payment_method.method_id,
                'type': method_type,
                'provider': provider
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_transaction_history(self, customer_id: str = None,
                                    limit: int = 50,
                                    offset: int = 0) -> Dict[str, Any]:
        """Get transaction history"""
        try:
            transactions = list(self.transactions.values())

            if customer_id:
                transactions = [t for t in transactions if t.customer_id == customer_id]

            # Sort by creation date (newest first)
            transactions.sort(key=lambda x: x.created_at, reverse=True)

            # Apply pagination
            paginated_transactions = transactions[offset:offset + limit]

            return {
                'transactions': [
                    {
                        'transaction_id': t.transaction_id,
                        'amount': t.amount,
                        'currency': t.currency,
                        'status': t.status,
                        'payment_method': t.payment_method,
                        'description': t.description,
                        'created_at': t.created_at.isoformat(),
                        'completed_at': t.completed_at.isoformat() if t.completed_at else None
                    }
                    for t in paginated_transactions
                ],
                'total_count': len(transactions),
                'limit': limit,
                'offset': offset
            }

        except Exception as e:
            return {'error': str(e), 'transactions': []}

    async def _send_payment_webhook(self, event_type: str, transaction: PaymentTransaction):
        """Send payment webhook event"""
        try:
            webhook_data = {
                'event_type': event_type,
                'transaction_id': transaction.transaction_id,
                'amount': transaction.amount,
                'currency': transaction.currency,
                'customer_id': transaction.customer_id,
                'status': transaction.status,
                'timestamp': datetime.now().isoformat(),
                'metadata': transaction.metadata
            }

            # Send to analytics
            await self.manager.execute_webhook('analytics_services', 'payment_event', webhook_data)

            # Send to other interested services
            await self.manager.execute_webhook('social_platforms', 'payment_notification', webhook_data)

        except Exception as e:
            self.logger.error(f"Error sending payment webhook: {e}")

    async def verify_webhook_signature(self, provider: str, payload: bytes,
                                     signature: str) -> bool:
        """Verify webhook signature"""
        try:
            if provider == 'stripe':
                return self._verify_stripe_webhook(payload, signature)
            elif provider == 'paypal':
                return self._verify_paypal_webhook(payload, signature)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error verifying webhook signature: {e}")
            return False

    def _verify_stripe_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            import stripe
            secret = self.webhook_secrets.get('stripe')
            if secret:
                event = stripe.Webhook.construct_event(
                    payload, signature, secret
                )
                return True
            return False
        except Exception:
            return False

    def _verify_paypal_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify PayPal webhook signature"""
        # PayPal webhook verification would go here
        # For now, return True for testing
        return True

    async def get_status(self) -> IntegrationStatus:
        """Get integration status"""
        return self.status

    async def enable(self):
        """Enable the integration"""
        self.status = IntegrationStatus.ACTIVE
        self.logger.info("Payment Systems Integration enabled")

    async def disable(self):
        """Disable the integration"""
        self.status = IntegrationStatus.INACTIVE
        self.logger.info("Payment Systems Integration disabled")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'providers': {},
            'metrics': {
                'total_transactions': len(self.transactions),
                'active_subscriptions': len([s for s in self.subscriptions.values() if s.status == 'active']),
                'pending_transactions': len([t for t in self.transactions.values() if t.status == 'pending'])
            }
        }

        # Check Stripe
        if self.stripe_client:
            try:
                # Test Stripe API
                self.stripe_client.Balance.retrieve()
                health_status['providers']['stripe'] = {'status': 'connected'}
            except Exception as e:
                health_status['providers']['stripe'] = {'status': 'error', 'error': str(e)}

        # Check PayPal
        if self.paypal_client:
            try:
                token = await self._get_paypal_access_token()
                health_status['providers']['paypal'] = {
                    'status': 'connected' if token else 'disconnected'
                }
            except Exception as e:
                health_status['providers']['paypal'] = {'status': 'error', 'error': str(e)}

        # Check Coinbase
        if self.coinbase_client:
            health_status['providers']['coinbase'] = {'status': 'configured'}

        return health_status

    async def check_rate_limit(self):
        """Check rate limits"""
        # Rate limiting would be implemented here
        pass

    async def handle_webhook(self, event_type: str, data: Dict[str, Any]):
        """Handle webhook events"""
        if event_type == 'stripe.webhook':
            await self._handle_stripe_webhook(data)
        elif event_type == 'paypal.webhook':
            await self._handle_paypal_webhook(data)

    async def _handle_stripe_webhook(self, data: Dict[str, Any]):
        """Handle Stripe webhook events"""
        try:
            event_type = data.get('type')
            event_data = data.get('data', {}).get('object', {})

            if event_type == 'payment_intent.succeeded':
                payment_intent_id = event_data.get('id')
                if payment_intent_id in self.transactions:
                    transaction = self.transactions[payment_intent_id]
                    transaction.status = 'completed'
                    transaction.completed_at = datetime.now()
                    await self._send_payment_webhook('payment.completed', transaction)

            elif event_type == 'payment_intent.payment_failed':
                payment_intent_id = event_data.get('id')
                if payment_intent_id in self.transactions:
                    transaction = self.transactions[payment_intent_id]
                    transaction.status = 'failed'
                    await self._send_payment_webhook('payment.failed', transaction)

            elif event_type == 'invoice.payment_succeeded':
                subscription_id = event_data.get('subscription')
                if subscription_id and subscription_id in self.subscriptions:
                    subscription = self.subscriptions[subscription_id]
                    subscription.status = 'active'
                    await self._send_payment_webhook('subscription.payment_succeeded', subscription)

        except Exception as e:
            self.logger.error(f"Error handling Stripe webhook: {e}")

    async def _handle_paypal_webhook(self, data: Dict[str, Any]):
        """Handle PayPal webhook events"""
        try:
            event_type = data.get('event_type')
            resource = data.get('resource', {})

            if event_type == 'PAYMENT.CAPTURE.COMPLETED':
                order_id = resource.get('supplementary_data', {}).get('related_ids', {}).get('order_id')
                if order_id and order_id in self.transactions:
                    transaction = self.transactions[order_id]
                    transaction.status = 'completed'
                    transaction.completed_at = datetime.now()
                    await self._send_payment_webhook('payment.completed', transaction)

        except Exception as e:
            self.logger.error(f"Error handling PayPal webhook: {e}")

    async def shutdown(self):
        """Shutdown the integration"""
        self.logger.info("Payment Systems Integration shutdown")