"""
Cryptocurrency Payment Integration System for FacultyFinder
===========================================================

Comprehensive crypto payment system supporting multiple providers:
- Coinbase Commerce
- NOWPayments
- CoinGate
- BitPay (optional)

Features:
- Multi-currency support (BTC, ETH, LTC, BCH, USDC, USDT, DAI, MATIC, BNB, DOGE)
- Real-time exchange rates
- Webhook processing
- Payment verification
- QR code generation
- Transaction tracking
"""

import os
import json
import time
import hmac
import hashlib
import logging
import requests
import qrcode
import io
import base64
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from cryptography.fernet import Fernet
from flask import current_app
import sqlite3

logger = logging.getLogger(__name__)

class CryptoPaymentError(Exception):
    """Base exception for crypto payment errors"""
    pass

class PaymentProviderError(CryptoPaymentError):
    """Payment provider specific errors"""
    pass

class ExchangeRateError(CryptoPaymentError):
    """Exchange rate fetching errors"""
    pass

class CryptoPaymentManager:
    """Main crypto payment manager handling multiple providers"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.providers = {}
        self.exchange_rate_cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Initialize encryption for API keys
        self.encryption_key = os.getenv('CRYPTO_ENCRYPTION_KEY', Fernet.generate_key())
        self.cipher = Fernet(self.encryption_key)
        
        # Initialize providers
        self._init_providers()
    
    def _init_providers(self):
        """Initialize payment providers"""
        try:
            # Coinbase Commerce
            coinbase_api_key = os.getenv('COINBASE_COMMERCE_API_KEY')
            if coinbase_api_key:
                self.providers['coinbase_commerce'] = CoinbaseCommerceProvider(
                    api_key=coinbase_api_key,
                    webhook_secret=os.getenv('COINBASE_COMMERCE_WEBHOOK_SECRET')
                )
            
            # NOWPayments
            nowpayments_api_key = os.getenv('NOWPAYMENTS_API_KEY')
            if nowpayments_api_key:
                self.providers['nowpayments'] = NOWPaymentsProvider(
                    api_key=nowpayments_api_key,
                    webhook_secret=os.getenv('NOWPAYMENTS_WEBHOOK_SECRET')
                )
            
            # CoinGate
            coingate_api_key = os.getenv('COINGATE_API_KEY')
            if coingate_api_key:
                self.providers['coingate'] = CoinGateProvider(
                    api_key=coingate_api_key,
                    webhook_secret=os.getenv('COINGATE_WEBHOOK_SECRET'),
                    sandbox=os.getenv('COINGATE_SANDBOX', 'true').lower() == 'true'
                )
                
            logger.info(f"Initialized {len(self.providers)} crypto payment providers")
            
        except Exception as e:
            logger.error(f"Error initializing crypto payment providers: {e}")
    
    def get_supported_currencies(self, provider_name: str = None) -> List[Dict]:
        """Get supported cryptocurrencies for a provider or all providers"""
        try:
            if not self.db:
                return []
            
            if provider_name:
                cursor = self.db.execute("""
                    SELECT cc.*, cpp.supported_currencies as provider_currencies
                    FROM crypto_currencies cc
                    JOIN crypto_payment_providers cpp ON cpp.name = ?
                    WHERE cc.is_active = 1 AND cpp.is_active = 1
                """, (provider_name,))
                
                provider_data = cursor.fetchone()
                if not provider_data:
                    return []
                
                supported_symbols = json.loads(provider_data['provider_currencies'])
                cursor = self.db.execute("""
                    SELECT * FROM crypto_currencies 
                    WHERE symbol IN ({}) AND is_active = 1
                    ORDER BY is_stablecoin DESC, symbol
                """.format(','.join(['?'] * len(supported_symbols))), supported_symbols)
                
            else:
                cursor = self.db.execute("""
                    SELECT * FROM crypto_currencies 
                    WHERE is_active = 1 
                    ORDER BY is_stablecoin DESC, symbol
                """)
            
            currencies = []
            for row in cursor.fetchall():
                currencies.append({
                    'id': row['id'],
                    'symbol': row['symbol'],
                    'name': row['name'],
                    'network': row['network'],
                    'decimals': row['decimals'],
                    'is_stablecoin': row['is_stablecoin'],
                    'logo_url': row['logo_url'],
                    'min_payment': float(row['min_payment_amount']),
                    'max_payment': float(row['max_payment_amount'])
                })
            
            return currencies
            
        except Exception as e:
            logger.error(f"Error getting supported currencies: {e}")
            return []
    
    def get_exchange_rate(self, crypto_symbol: str, fiat_currency: str = 'CAD') -> Decimal:
        """Get exchange rate for crypto to fiat with caching"""
        cache_key = f"{crypto_symbol}_{fiat_currency}"
        
        # Check cache first
        if cache_key in self.exchange_rate_cache:
            rate_data = self.exchange_rate_cache[cache_key]
            if time.time() - rate_data['timestamp'] < self.cache_duration:
                return Decimal(str(rate_data['rate']))
        
        try:
            # Try multiple sources for exchange rate
            rate = None
            
            # Source 1: CoinGecko (free, reliable)
            try:
                rate = self._get_coingecko_rate(crypto_symbol, fiat_currency)
            except Exception as e:
                logger.warning(f"CoinGecko rate fetch failed: {e}")
            
            # Source 2: CoinAPI (backup)
            if not rate:
                try:
                    rate = self._get_coinapi_rate(crypto_symbol, fiat_currency)
                except Exception as e:
                    logger.warning(f"CoinAPI rate fetch failed: {e}")
            
            # Source 3: Coinbase (backup)
            if not rate:
                try:
                    rate = self._get_coinbase_rate(crypto_symbol, fiat_currency)
                except Exception as e:
                    logger.warning(f"Coinbase rate fetch failed: {e}")
            
            if not rate:
                raise ExchangeRateError(f"Unable to fetch exchange rate for {crypto_symbol}/{fiat_currency}")
            
            # Cache the rate
            self.exchange_rate_cache[cache_key] = {
                'rate': float(rate),
                'timestamp': time.time()
            }
            
            # Store in database
            if self.db:
                self._store_exchange_rate(crypto_symbol, fiat_currency, rate, 'coingecko')
            
            return rate
            
        except Exception as e:
            logger.error(f"Error getting exchange rate for {crypto_symbol}: {e}")
            
            # Try to get last known rate from database
            if self.db:
                cursor = self.db.execute("""
                    SELECT rate FROM crypto_exchange_rates cer
                    JOIN crypto_currencies cc ON cc.id = cer.currency_id
                    WHERE cc.symbol = ? AND cer.fiat_currency = ?
                    ORDER BY cer.created_at DESC
                    LIMIT 1
                """, (crypto_symbol, fiat_currency))
                
                row = cursor.fetchone()
                if row:
                    logger.info(f"Using cached exchange rate for {crypto_symbol}")
                    return Decimal(str(row['rate']))
            
            raise ExchangeRateError(f"No exchange rate available for {crypto_symbol}")
    
    def _get_coingecko_rate(self, crypto_symbol: str, fiat_currency: str) -> Decimal:
        """Get exchange rate from CoinGecko"""
        # Map symbols to CoinGecko IDs
        symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'USDC': 'usd-coin',
            'USDT': 'tether',
            'DAI': 'dai',
            'MATIC': 'matic-network',
            'BNB': 'binancecoin',
            'DOGE': 'dogecoin'
        }
        
        coin_id = symbol_map.get(crypto_symbol.upper())
        if not coin_id:
            raise ExchangeRateError(f"Unsupported symbol: {crypto_symbol}")
        
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': fiat_currency.lower()
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if coin_id not in data or fiat_currency.lower() not in data[coin_id]:
            raise ExchangeRateError(f"Rate not found in CoinGecko response")
        
        return Decimal(str(data[coin_id][fiat_currency.lower()]))
    
    def _get_coinapi_rate(self, crypto_symbol: str, fiat_currency: str) -> Decimal:
        """Get exchange rate from CoinAPI (requires API key)"""
        api_key = os.getenv('COINAPI_KEY')
        if not api_key:
            raise ExchangeRateError("CoinAPI key not configured")
        
        url = f"https://rest.coinapi.io/v1/exchangerate/{crypto_symbol}/{fiat_currency}"
        headers = {'X-CoinAPI-Key': api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return Decimal(str(data['rate']))
    
    def _get_coinbase_rate(self, crypto_symbol: str, fiat_currency: str) -> Decimal:
        """Get exchange rate from Coinbase"""
        url = f"https://api.coinbase.com/v2/exchange-rates"
        params = {'currency': crypto_symbol}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if fiat_currency not in data['data']['rates']:
            raise ExchangeRateError(f"Rate not found for {fiat_currency}")
        
        return Decimal(str(data['data']['rates'][fiat_currency]))
    
    def _store_exchange_rate(self, crypto_symbol: str, fiat_currency: str, rate: Decimal, source: str):
        """Store exchange rate in database"""
        try:
            if not self.db:
                return
            
            # Get currency ID
            cursor = self.db.execute("SELECT id FROM crypto_currencies WHERE symbol = ?", (crypto_symbol,))
            row = cursor.fetchone()
            if not row:
                return
            
            currency_id = row['id']
            
            # Update or insert rate
            self.db.execute("""
                INSERT OR REPLACE INTO crypto_exchange_rates 
                (currency_id, fiat_currency, rate, source, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (currency_id, fiat_currency, float(rate), source))
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing exchange rate: {e}")
    
    def create_payment(self, user_id: int, amount_cad: int, service_type: str, 
                      currency_symbol: str, provider_name: str = 'coinbase_commerce',
                      service_details: Dict = None) -> Dict:
        """Create a new crypto payment"""
        try:
            if provider_name not in self.providers:
                raise PaymentProviderError(f"Provider {provider_name} not available")
            
            provider = self.providers[provider_name]
            
            # Get exchange rate
            exchange_rate = self.get_exchange_rate(currency_symbol, 'CAD')
            crypto_amount = Decimal(amount_cad / 100) / exchange_rate
            
            # Get currency info
            cursor = self.db.execute(
                "SELECT * FROM crypto_currencies WHERE symbol = ? AND is_active = 1",
                (currency_symbol,)
            )
            currency = cursor.fetchone()
            if not currency:
                raise CryptoPaymentError(f"Currency {currency_symbol} not supported")
            
            # Round to appropriate decimals
            crypto_amount = crypto_amount.quantize(
                Decimal('0.1') ** currency['decimals'], 
                rounding=ROUND_DOWN
            )
            
            # Check minimum/maximum amounts
            if crypto_amount < Decimal(str(currency['min_payment_amount'])):
                raise CryptoPaymentError(f"Amount below minimum ({currency['min_payment_amount']} {currency_symbol})")
            if crypto_amount > Decimal(str(currency['max_payment_amount'])):
                raise CryptoPaymentError(f"Amount above maximum ({currency['max_payment_amount']} {currency_symbol})")
            
            # Create payment with provider
            payment_data = provider.create_charge(
                amount=float(crypto_amount),
                currency=currency_symbol,
                description=f"FacultyFinder {service_type.replace('_', ' ').title()}",
                metadata={
                    'user_id': user_id,
                    'service_type': service_type,
                    'service_details': json.dumps(service_details or {})
                }
            )
            
            # Store in database
            payment_id = self._store_payment(
                user_id=user_id,
                provider_name=provider_name,
                currency_symbol=currency_symbol,
                amount_requested=float(crypto_amount),
                fiat_amount=amount_cad,
                exchange_rate=float(exchange_rate),
                service_type=service_type,
                service_details=service_details,
                payment_data=payment_data
            )
            
            # Generate QR code
            qr_code = self._generate_qr_code(payment_data.get('payment_address', ''))
            
            return {
                'payment_id': payment_id,
                'crypto_amount': float(crypto_amount),
                'currency': currency_symbol,
                'exchange_rate': float(exchange_rate),
                'payment_address': payment_data.get('payment_address'),
                'payment_url': payment_data.get('hosted_url'),
                'expires_at': payment_data.get('expires_at'),
                'qr_code': qr_code,
                'provider': provider_name
            }
            
        except Exception as e:
            logger.error(f"Error creating crypto payment: {e}")
            raise CryptoPaymentError(f"Failed to create payment: {str(e)}")
    
    def _store_payment(self, user_id: int, provider_name: str, currency_symbol: str,
                      amount_requested: float, fiat_amount: int, exchange_rate: float,
                      service_type: str, service_details: Dict, payment_data: Dict) -> str:
        """Store payment in database"""
        try:
            # Get IDs
            cursor = self.db.execute("SELECT id FROM crypto_currencies WHERE symbol = ?", (currency_symbol,))
            currency_id = cursor.fetchone()['id']
            
            cursor = self.db.execute("SELECT id FROM crypto_payment_providers WHERE name = ?", (provider_name,))
            provider_id = cursor.fetchone()['id']
            
            # Generate unique payment ID
            payment_id = payment_data.get('id', f"ff_{int(time.time())}_{user_id}")
            
            # Calculate expiry (usually 15 minutes for crypto)
            expires_at = datetime.now() + timedelta(minutes=15)
            if 'expires_at' in payment_data:
                expires_at = datetime.fromisoformat(payment_data['expires_at'].replace('Z', '+00:00'))
            
            cursor = self.db.execute("""
                INSERT INTO crypto_payments (
                    user_id, payment_id, provider_id, currency_id,
                    amount_requested, fiat_amount, fiat_currency, exchange_rate,
                    service_type, service_details, status,
                    payment_address, provider_charge_id, provider_checkout_url,
                    provider_hosted_url, provider_data, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, payment_id, provider_id, currency_id,
                amount_requested, fiat_amount, 'CAD', exchange_rate,
                service_type, json.dumps(service_details or {}), 'pending',
                payment_data.get('payment_address'),
                payment_data.get('id'),
                payment_data.get('checkout_url'),
                payment_data.get('hosted_url'),
                json.dumps(payment_data),
                expires_at
            ))
            
            self.db.commit()
            return payment_id
            
        except Exception as e:
            logger.error(f"Error storing payment: {e}")
            raise
    
    def _generate_qr_code(self, payment_address: str) -> str:
        """Generate QR code for payment address"""
        try:
            if not payment_address:
                return ""
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(payment_address)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return ""
    
    def verify_webhook(self, provider_name: str, payload: str, signature: str, headers: Dict) -> bool:
        """Verify webhook signature"""
        if provider_name not in self.providers:
            return False
        
        return self.providers[provider_name].verify_webhook(payload, signature, headers)
    
    def process_webhook(self, provider_name: str, event_data: Dict) -> bool:
        """Process webhook event"""
        try:
            if provider_name not in self.providers:
                logger.error(f"Unknown provider: {provider_name}")
                return False
            
            provider = self.providers[provider_name]
            payment_update = provider.process_webhook_event(event_data)
            
            if not payment_update:
                return True  # Event processed but no update needed
            
            # Update payment in database
            return self._update_payment_status(
                payment_id=payment_update['payment_id'],
                status=payment_update['status'],
                transaction_hash=payment_update.get('transaction_hash'),
                amount_received=payment_update.get('amount_received'),
                confirmations=payment_update.get('confirmations', 0)
            )
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return False
    
    def _update_payment_status(self, payment_id: str, status: str, transaction_hash: str = None,
                             amount_received: float = None, confirmations: int = 0) -> bool:
        """Update payment status in database"""
        try:
            update_fields = ["status = ?"]
            params = [status]
            
            if transaction_hash:
                update_fields.append("transaction_hash = ?")
                params.append(transaction_hash)
            
            if amount_received is not None:
                update_fields.append("amount_received = ?")
                params.append(amount_received)
            
            if confirmations > 0:
                update_fields.append("confirmations = ?")
                params.append(confirmations)
            
            if status == 'completed':
                update_fields.append("completed_at = CURRENT_TIMESTAMP")
            elif status in ['confirming', 'confirmed']:
                update_fields.append("confirmed_at = CURRENT_TIMESTAMP")
            
            params.append(payment_id)
            
            cursor = self.db.execute(f"""
                UPDATE crypto_payments 
                SET {', '.join(update_fields)}
                WHERE payment_id = ?
            """, params)
            
            self.db.commit()
            
            # If payment completed, trigger any post-payment actions
            if status == 'completed':
                self._handle_payment_completion(payment_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
            return False
    
    def _handle_payment_completion(self, payment_id: str):
        """Handle actions after payment completion"""
        try:
            # Get payment details
            cursor = self.db.execute("""
                SELECT cp.*, u.email, u.username
                FROM crypto_payments cp
                LEFT JOIN users u ON u.id = cp.user_id
                WHERE cp.payment_id = ?
            """, (payment_id,))
            
            payment = cursor.fetchone()
            if not payment:
                return
            
            # Log activity
            if payment['user_id']:
                self.db.execute("""
                    INSERT INTO user_activity_log (user_id, activity_type, activity_data)
                    VALUES (?, 'crypto_payment_completed', ?)
                """, (
                    payment['user_id'],
                    json.dumps({
                        'payment_id': payment_id,
                        'service_type': payment['service_type'],
                        'amount': payment['fiat_amount'],
                        'currency': payment['fiat_currency']
                    })
                ))
                self.db.commit()
            
            logger.info(f"Crypto payment completed: {payment_id}")
            
        except Exception as e:
            logger.error(f"Error handling payment completion: {e}")


class CoinbaseCommerceProvider:
    """Coinbase Commerce payment provider"""
    
    def __init__(self, api_key: str, webhook_secret: str = None):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.base_url = "https://api.commerce.coinbase.com"
        self.headers = {
            'X-CC-Api-Key': api_key,
            'X-CC-Version': '2018-03-22',
            'Content-Type': 'application/json'
        }
    
    def create_charge(self, amount: float, currency: str, description: str, metadata: Dict) -> Dict:
        """Create a charge in Coinbase Commerce"""
        try:
            data = {
                'name': description,
                'description': description,
                'pricing_type': 'fixed_price',
                'local_price': {
                    'amount': str(amount),
                    'currency': currency.upper()
                },
                'metadata': metadata
            }
            
            response = requests.post(
                f"{self.base_url}/charges",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            charge = result['data']
            payment_address = charge['addresses'].get(currency.upper(), '')
            
            return {
                'id': charge['id'],
                'payment_address': payment_address,
                'hosted_url': charge['hosted_url'],
                'expires_at': charge['expires_at'],
                'checkout_url': charge['hosted_url']
            }
            
        except Exception as e:
            logger.error(f"Coinbase Commerce charge creation failed: {e}")
            raise PaymentProviderError(f"Coinbase Commerce error: {str(e)}")
    
    def verify_webhook(self, payload: str, signature: str, headers: Dict) -> bool:
        """Verify Coinbase Commerce webhook signature"""
        if not self.webhook_secret:
            return True  # Skip verification if no secret
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Webhook verification failed: {e}")
            return False
    
    def process_webhook_event(self, event_data: Dict) -> Optional[Dict]:
        """Process Coinbase Commerce webhook event"""
        try:
            event_type = event_data.get('type')
            charge = event_data.get('data', {})
            
            if not charge or 'id' not in charge:
                return None
            
            status_map = {
                'charge:created': 'pending',
                'charge:confirmed': 'confirming',
                'charge:completed': 'completed',
                'charge:failed': 'failed',
                'charge:expired': 'expired'
            }
            
            if event_type not in status_map:
                return None
            
            # Get transaction details
            payments = charge.get('payments', [])
            transaction_hash = None
            amount_received = None
            
            if payments:
                latest_payment = payments[-1]
                transaction_hash = latest_payment.get('transaction_id')
                amount_received = float(latest_payment.get('value', {}).get('local', {}).get('amount', 0))
            
            return {
                'payment_id': charge['id'],
                'status': status_map[event_type],
                'transaction_hash': transaction_hash,
                'amount_received': amount_received,
                'confirmations': len(payments)
            }
            
        except Exception as e:
            logger.error(f"Error processing Coinbase webhook: {e}")
            return None


class NOWPaymentsProvider:
    """NOWPayments provider"""
    
    def __init__(self, api_key: str, webhook_secret: str = None):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.base_url = "https://api.nowpayments.io/v1"
        self.headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
    
    def create_charge(self, amount: float, currency: str, description: str, metadata: Dict) -> Dict:
        """Create a payment in NOWPayments"""
        try:
            # First get minimum payment amount
            response = requests.get(
                f"{self.base_url}/min-amount",
                headers=self.headers,
                params={'currency_from': currency.lower(), 'currency_to': currency.lower()},
                timeout=30
            )
            response.raise_for_status()
            min_amount = float(response.json().get('min_amount', 0))
            
            if amount < min_amount:
                raise PaymentProviderError(f"Amount below minimum: {min_amount} {currency}")
            
            # Create payment
            data = {
                'price_amount': amount,
                'price_currency': currency.lower(),
                'pay_currency': currency.lower(),
                'order_id': f"ff_{int(time.time())}_{metadata.get('user_id', 'guest')}",
                'order_description': description
            }
            
            response = requests.post(
                f"{self.base_url}/payment",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                'id': result['payment_id'],
                'payment_address': result['pay_address'],
                'hosted_url': result.get('invoice_url', ''),
                'expires_at': (datetime.now() + timedelta(minutes=15)).isoformat(),
                'checkout_url': result.get('invoice_url', '')
            }
            
        except Exception as e:
            logger.error(f"NOWPayments charge creation failed: {e}")
            raise PaymentProviderError(f"NOWPayments error: {str(e)}")
    
    def verify_webhook(self, payload: str, signature: str, headers: Dict) -> bool:
        """Verify NOWPayments webhook signature"""
        # NOWPayments uses different signature verification
        # Implementation depends on their specific method
        return True  # Simplified for now
    
    def process_webhook_event(self, event_data: Dict) -> Optional[Dict]:
        """Process NOWPayments webhook event"""
        try:
            payment_status = event_data.get('payment_status')
            payment_id = event_data.get('payment_id')
            
            if not payment_id:
                return None
            
            status_map = {
                'waiting': 'pending',
                'confirming': 'confirming',
                'confirmed': 'confirmed',
                'finished': 'completed',
                'failed': 'failed',
                'expired': 'expired'
            }
            
            if payment_status not in status_map:
                return None
            
            return {
                'payment_id': payment_id,
                'status': status_map[payment_status],
                'transaction_hash': event_data.get('pay_tx_id'),
                'amount_received': float(event_data.get('actually_paid', 0)),
                'confirmations': int(event_data.get('outcome_amount', 0))
            }
            
        except Exception as e:
            logger.error(f"Error processing NOWPayments webhook: {e}")
            return None


class CoinGateProvider:
    """CoinGate payment provider"""
    
    def __init__(self, api_key: str, webhook_secret: str = None, sandbox: bool = True):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.sandbox = sandbox
        
        if sandbox:
            self.base_url = "https://api-sandbox.coingate.com/v2"
        else:
            self.base_url = "https://api.coingate.com/v2"
        
        self.headers = {
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_charge(self, amount: float, currency: str, description: str, metadata: Dict) -> Dict:
        """Create an order in CoinGate"""
        try:
            data = {
                'order_id': f"ff_{int(time.time())}_{metadata.get('user_id', 'guest')}",
                'price_amount': amount,
                'price_currency': currency.upper(),
                'receive_currency': currency.upper(),
                'title': description,
                'description': description,
                'success_url': f"{os.getenv('BASE_URL', 'http://localhost:8080')}/payment/success",
                'cancel_url': f"{os.getenv('BASE_URL', 'http://localhost:8080')}/payment/cancel",
                'callback_url': f"{os.getenv('BASE_URL', 'http://localhost:8080')}/webhooks/coingate"
            }
            
            response = requests.post(
                f"{self.base_url}/orders",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                'id': str(result['id']),
                'payment_address': result.get('payment_address', ''),
                'hosted_url': result.get('payment_url', ''),
                'expires_at': (datetime.now() + timedelta(minutes=15)).isoformat(),
                'checkout_url': result.get('payment_url', '')
            }
            
        except Exception as e:
            logger.error(f"CoinGate order creation failed: {e}")
            raise PaymentProviderError(f"CoinGate error: {str(e)}")
    
    def verify_webhook(self, payload: str, signature: str, headers: Dict) -> bool:
        """Verify CoinGate webhook signature"""
        # CoinGate webhook verification implementation
        return True  # Simplified for now
    
    def process_webhook_event(self, event_data: Dict) -> Optional[Dict]:
        """Process CoinGate webhook event"""
        try:
            status = event_data.get('status')
            order_id = str(event_data.get('id', ''))
            
            if not order_id:
                return None
            
            status_map = {
                'new': 'pending',
                'pending': 'pending',
                'confirming': 'confirming',
                'paid': 'completed',
                'invalid': 'failed',
                'expired': 'expired',
                'canceled': 'failed'
            }
            
            if status not in status_map:
                return None
            
            return {
                'payment_id': order_id,
                'status': status_map[status],
                'transaction_hash': event_data.get('payment_id'),
                'amount_received': float(event_data.get('receive_amount', 0))
            }
            
        except Exception as e:
            logger.error(f"Error processing CoinGate webhook: {e}")
            return None


# Utility functions
def get_crypto_payment_manager(db_connection=None) -> CryptoPaymentManager:
    """Get a configured crypto payment manager instance"""
    return CryptoPaymentManager(db_connection)

def format_crypto_amount(amount: float, decimals: int = 8) -> str:
    """Format crypto amount with appropriate precision"""
    if amount == 0:
        return "0"
    
    # Remove trailing zeros
    formatted = f"{amount:.{decimals}f}".rstrip('0').rstrip('.')
    return formatted

def get_crypto_logo_url(symbol: str) -> str:
    """Get logo URL for cryptocurrency"""
    logos = {
        'BTC': 'https://cryptologos.cc/logos/bitcoin-btc-logo.png',
        'ETH': 'https://cryptologos.cc/logos/ethereum-eth-logo.png',
        'LTC': 'https://cryptologos.cc/logos/litecoin-ltc-logo.png',
        'BCH': 'https://cryptologos.cc/logos/bitcoin-cash-bch-logo.png',
        'USDC': 'https://cryptologos.cc/logos/usd-coin-usdc-logo.png',
        'USDT': 'https://cryptologos.cc/logos/tether-usdt-logo.png',
        'DAI': 'https://cryptologos.cc/logos/multi-collateral-dai-dai-logo.png',
        'MATIC': 'https://cryptologos.cc/logos/polygon-matic-logo.png',
        'BNB': 'https://cryptologos.cc/logos/bnb-bnb-logo.png',
        'DOGE': 'https://cryptologos.cc/logos/dogecoin-doge-logo.png'
    }
    return logos.get(symbol.upper(), '') 