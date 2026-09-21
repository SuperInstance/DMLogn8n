#!/usr/bin/env python3
"""
CDN Manager Integration
Connects with Cloudflare, AWS CloudFront, Fastly, and other CDN providers
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import hashlib
import mimetypes
import os
from .integration_manager import IntegrationStatus

@dataclass
class CDNAsset:
    asset_id: str
    url: str
    file_path: str
    file_size: int
    content_type: str
    checksum: str
    provider: str
    cache_ttl: int
    created_at: datetime
    last_accessed: Optional[datetime]
    access_count: int

@dataclass
class CDNZone:
    zone_id: str
    domain: str
    provider: str
    status: str
    nameservers: List[str]
    ssl_status: str
    cache_settings: Dict[str, Any]

class CDNManager:
    """Integration with CDN providers for global content delivery"""

    def __init__(self, integration_manager):
        self.manager = integration_manager
        self.logger = logging.getLogger(__name__)
        self.config = {}
        self.status = IntegrationStatus.INACTIVE

        # CDN provider clients
        self.cloudflare_client = None
        self.aws_client = None
        self.fastly_client = None

        # Asset tracking
        self.assets: Dict[str, CDNAsset] = {}
        self.zones: Dict[str, CDNZone] = {}

        # Cache management
        self.cache_stats = {
            'total_assets': 0,
            'cache_hit_rate': 0.0,
            'bandwidth_saved': 0,
            'total_requests': 0
        }

    async def initialize(self):
        """Initialize the CDN manager"""
        self.logger.info("Initializing CDN Manager")

        # Initialize Cloudflare
        await self._initialize_cloudflare()

        # Initialize AWS CloudFront
        await self._initialize_aws()

        # Initialize Fastly
        await self._initialize_fastly()

        # Load existing zones
        await self._load_zones()

        # Start cache optimization
        asyncio.create_task(self._cache_optimization_loop())

        self.status = IntegrationStatus.ACTIVE

    async def _initialize_cloudflare(self):
        """Initialize Cloudflare CDN"""
        try:
            api_token = self.config.get('api_keys', {}).get('cloudflare_api_token')
            if api_token:
                self.cloudflare_client = {
                    'api_token': api_token,
                    'base_url': 'https://api.cloudflare.com/client/v4'
                }
                self.logger.info("Cloudflare CDN initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Cloudflare: {e}")

    async def _initialize_aws(self):
        """Initialize AWS CloudFront"""
        try:
            access_key = self.config.get('api_keys', {}).get('aws_access_key')
            secret_key = self.config.get('api_keys', {}).get('aws_secret_key')
            region = self.config.get('aws_region', 'us-east-1')

            if access_key and secret_key:
                self.aws_client = {
                    'access_key': access_key,
                    'secret_key': secret_key,
                    'region': region,
                    'base_url': f'https://cloudfront.amazonaws.com/2020-05-31'
                }
                self.logger.info("AWS CloudFront initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS CloudFront: {e}")

    async def _initialize_fastly(self):
        """Initialize Fastly CDN"""
        try:
            api_key = self.config.get('api_keys', {}).get('fastly_api_key')
            if api_key:
                self.fastly_client = {
                    'api_key': api_key,
                    'base_url': 'https://api.fastly.com'
                }
                self.logger.info("Fastly CDN initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Fastly: {e}")

    async def _load_zones(self):
        """Load existing CDN zones"""
        try:
            # Load zones from cache
            cached_zones = await self.manager.cache_get('cdn_zones')
            if cached_zones:
                for zone_data in cached_zones:
                    zone = CDNZone(**zone_data)
                    self.zones[zone.zone_id] = zone

            # Load assets from cache
            cached_assets = await self.manager.cache_get('cdn_assets')
            if cached_assets:
                for asset_data in cached_assets:
                    asset = CDNAsset(**asset_data)
                    self.assets[asset.asset_id] = asset

        except Exception as e:
            self.logger.error(f"Error loading zones: {e}")

    async def upload_asset(self, file_path: str,
                          provider: str = 'cloudflare',
                          cache_ttl: int = 86400,
                          custom_domain: str = None) -> Dict[str, Any]:
        """Upload an asset to CDN"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}

            # Calculate file properties
            file_size = os.path.getsize(file_path)
            checksum = await self._calculate_file_checksum(file_path)
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

            # Check if asset already exists
            existing_asset = await self._find_existing_asset(checksum, provider)
            if existing_asset:
                return {
                    'success': True,
                    'asset_id': existing_asset.asset_id,
                    'url': existing_asset.url,
                    'message': 'Asset already exists'
                }

            # Upload to provider
            if provider == 'cloudflare' and self.cloudflare_client:
                result = await self._upload_to_cloudflare(file_path, content_type, cache_ttl)
            elif provider == 'aws' and self.aws_client:
                result = await self._upload_to_aws(file_path, content_type, cache_ttl)
            elif provider == 'fastly' and self.fastly_client:
                result = await self._upload_to_fastly(file_path, content_type, cache_ttl)
            else:
                return {'success': False, 'error': f'Provider {provider} not available'}

            if result['success']:
                # Create asset record
                asset = CDNAsset(
                    asset_id=result['asset_id'],
                    url=result['url'],
                    file_path=file_path,
                    file_size=file_size,
                    content_type=content_type,
                    checksum=checksum,
                    provider=provider,
                    cache_ttl=cache_ttl,
                    created_at=datetime.now(),
                    last_accessed=None,
                    access_count=0
                )

                self.assets[asset.asset_id] = asset

                # Update cache
                await self._update_asset_cache()

                # Track upload event
                await self.manager.execute_webhook('analytics_services', 'cdn_upload', {
                    'asset_id': asset.asset_id,
                    'provider': provider,
                    'file_size': file_size,
                    'content_type': content_type
                })

            return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    async def _find_existing_asset(self, checksum: str, provider: str) -> Optional[CDNAsset]:
        """Find existing asset by checksum"""
        for asset in self.assets.values():
            if asset.checksum == checksum and asset.provider == provider:
                return asset
        return None

    async def _upload_to_cloudflare(self, file_path: str, content_type: str,
                                  cache_ttl: int) -> Dict[str, Any]:
        """Upload asset to Cloudflare"""
        try:
            # Cloudflare upload logic would go here
            # For now, return mock data
            asset_id = f"cf_{int(datetime.now().timestamp())}"
            url = f"https://cdn.example.com/{asset_id}"

            return {
                'success': True,
                'asset_id': asset_id,
                'url': url,
                'provider': 'cloudflare'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _upload_to_aws(self, file_path: str, content_type: str,
                           cache_ttl: int) -> Dict[str, Any]:
        """Upload asset to AWS CloudFront/S3"""
        try:
            # AWS upload logic would go here
            # For now, return mock data
            asset_id = f"aws_{int(datetime.now().timestamp())}"
            url = f"https://d1234567890.cloudfront.net/{asset_id}"

            return {
                'success': True,
                'asset_id': asset_id,
                'url': url,
                'provider': 'aws'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _upload_to_fastly(self, file_path: str, content_type: str,
                              cache_ttl: int) -> Dict[str, Any]:
        """Upload asset to Fastly"""
        try:
            # Fastly upload logic would go here
            # For now, return mock data
            asset_id = f"fastly_{int(datetime.now().timestamp())}"
            url = f"https://fastly.example.com/{asset_id}"

            return {
                'success': True,
                'asset_id': asset_id,
                'url': url,
                'provider': 'fastly'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def purge_asset(self, asset_id: str, provider: str = None) -> Dict[str, Any]:
        """Purge/clear cache for an asset"""
        try:
            if asset_id not in self.assets:
                return {'success': False, 'error': 'Asset not found'}

            asset = self.assets[asset_id]
            target_provider = provider or asset.provider

            # Purge from provider
            if target_provider == 'cloudflare' and self.cloudflare_client:
                result = await self._purge_from_cloudflare(asset_id)
            elif target_provider == 'aws' and self.aws_client:
                result = await self._purge_from_aws(asset_id)
            elif target_provider == 'fastly' and self.fastly_client:
                result = await self._purge_from_fastly(asset_id)
            else:
                return {'success': False, 'error': f'Provider {target_provider} not available'}

            if result['success']:
                # Update asset access
                asset.last_accessed = datetime.now()
                asset.access_count += 1

            return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _purge_from_cloudflare(self, asset_id: str) -> Dict[str, Any]:
        """Purge asset from Cloudflare cache"""
        try:
            headers = {
                'Authorization': f'Bearer {self.cloudflare_client["api_token"]}',
                'Content-Type': 'application/json'
            }

            purge_data = {
                'files': [f"https://cdn.example.com/{asset_id}"]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.cloudflare_client['base_url']}/zones/purge_cache",
                    headers=headers,
                    json=purge_data
                ) as response:
                    if response.status == 200:
                        return {'success': True, 'provider': 'cloudflare'}
                    else:
                        error_text = await response.text()
                        return {'success': False, 'error': f"Cloudflare error: {error_text}"}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _purge_from_aws(self, asset_id: str) -> Dict[str, Any]:
        """Purge asset from AWS CloudFront cache"""
        try:
            # AWS CloudFront invalidation logic would go here
            return {'success': True, 'provider': 'aws'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _purge_from_fastly(self, asset_id: str) -> Dict[str, Any]:
        """Purge asset from Fastly cache"""
        try:
            # Fastly purge logic would go here
            return {'success': True, 'provider': 'fastly'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def create_zone(self, domain: str, provider: str = 'cloudflare',
                         cache_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new CDN zone"""
        try:
            zone_id = f"{provider}_{domain.replace('.', '_')}_{int(datetime.now().timestamp())}"

            # Create zone on provider
            if provider == 'cloudflare' and self.cloudflare_client:
                result = await self._create_cloudflare_zone(domain)
            elif provider == 'aws' and self.aws_client:
                result = await self._create_aws_distribution(domain)
            elif provider == 'fastly' and self.fastly_client:
                result = await self._create_fastly_service(domain)
            else:
                return {'success': False, 'error': f'Provider {provider} not available'}

            if result['success']:
                # Create zone record
                zone = CDNZone(
                    zone_id=zone_id,
                    domain=domain,
                    provider=provider,
                    status='active',
                    nameservers=result.get('nameservers', []),
                    ssl_status='active',
                    cache_settings=cache_settings or {}
                )

                self.zones[zone_id] = zone

                # Update cache
                await self._update_zone_cache()

                # Track zone creation
                await self.manager.execute_webhook('analytics_services', 'cdn_zone_created', {
                    'zone_id': zone_id,
                    'domain': domain,
                    'provider': provider
                })

            return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _create_cloudflare_zone(self, domain: str) -> Dict[str, Any]:
        """Create Cloudflare zone"""
        try:
            headers = {
                'Authorization': f'Bearer {self.cloudflare_client["api_token"]}',
                'Content-Type': 'application/json'
            }

            zone_data = {
                'name': domain,
                'account': {'id': 'account_id'},  # Would get from config
                'jump_start': True,
                'type': 'full'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.cloudflare_client['base_url']}/zones",
                    headers=headers,
                    json=zone_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'zone_id': result['result']['id'],
                            'nameservers': result['result']['name_servers'],
                            'provider': 'cloudflare'
                        }
                    else:
                        error_text = await response.text()
                        return {'success': False, 'error': f"Cloudflare error: {error_text}"}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _create_aws_distribution(self, domain: str) -> Dict[str, Any]:
        """Create AWS CloudFront distribution"""
        try:
            # AWS CloudFront distribution creation logic would go here
            return {
                'success': True,
                'distribution_id': f'distribution_{int(datetime.now().timestamp())}',
                'domain_name': f'd{int(datetime.now().timestamp())}.cloudfront.net',
                'provider': 'aws'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _create_fastly_service(self, domain: str) -> Dict[str, Any]:
        """Create Fastly service"""
        try:
            # Fastly service creation logic would go here
            return {
                'success': True,
                'service_id': f'service_{int(datetime.now().timestamp())}',
                'domain': domain,
                'provider': 'fastly'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_zone_stats(self, zone_id: str,
                           start_date: datetime = None,
                           end_date: datetime = None) -> Dict[str, Any]:
        """Get statistics for a specific zone"""
        try:
            if zone_id not in self.zones:
                return {'error': 'Zone not found'}

            zone = self.zones[zone_id]

            # Mock statistics data
            stats = {
                'zone_id': zone_id,
                'domain': zone.domain,
                'provider': zone.provider,
                'requests': {
                    'total': 1000000,
                    'cached': 850000,
                    'uncached': 150000,
                    'cache_hit_rate': 0.85
                },
                'bandwidth': {
                    'total_gb': 500,
                    'cached_gb': 425,
                    'saved_gb': 75
                },
                'response_times': {
                    'average_ms': 120,
                    'p50_ms': 80,
                    'p95_ms': 300,
                    'p99_ms': 800
                },
                'top_files': [
                    {'path': '/images/banner.jpg', 'requests': 50000},
                    {'path': '/css/main.css', 'requests': 45000},
                    {'path': '/js/app.js', 'requests': 40000}
                ],
                'time_period': f"{start_date} to {end_date}" if start_date and end_date else "Last 30 days"
            }

            return stats

        except Exception as e:
            return {'error': str(e)}

    async def optimize_cache(self, zone_id: str = None) -> Dict[str, Any]:
        """Optimize cache settings"""
        try:
            optimizations = []

            if zone_id:
                # Optimize specific zone
                if zone_id in self.zones:
                    zone = self.zones[zone_id]
                    optimization = await self._optimize_zone_cache(zone)
                    optimizations.append(optimization)
            else:
                # Optimize all zones
                for zone in self.zones.values():
                    optimization = await self._optimize_zone_cache(zone)
                    optimizations.append(optimization)

            return {
                'success': True,
                'optimizations': optimizations,
                'message': f"Optimized {len(optimizations)} zones"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _optimize_zone_cache(self, zone: CDNZone) -> Dict[str, Any]:
        """Optimize cache settings for a zone"""
        try:
            # Analyze access patterns
            zone_assets = [asset for asset in self.assets.values() if asset.provider == zone.provider]

            # Calculate optimal cache TTLs based on access patterns
            optimizations = []
            for asset in zone_assets:
                if asset.access_count > 100:  # Frequently accessed
                    if asset.cache_ttl < 3600:  # Less than 1 hour
                        # Increase cache TTL for frequently accessed assets
                        new_ttl = min(asset.cache_ttl * 2, 86400)  # Max 24 hours
                        asset.cache_ttl = new_ttl
                        optimizations.append({
                            'asset_id': asset.asset_id,
                            'type': 'cache_ttl_increased',
                            'old_ttl': asset.cache_ttl // 2,
                            'new_ttl': new_ttl
                        })

            return {
                'zone_id': zone.zone_id,
                'domain': zone.domain,
                'optimizations_count': len(optimizations),
                'optimizations': optimizations
            }

        except Exception as e:
            return {'error': str(e)}

    async def _cache_optimization_loop(self):
        """Background loop for cache optimization"""
        while True:
            try:
                # Run optimization every hour
                await asyncio.sleep(3600)
                await self.optimize_cache()
                self.logger.debug("Cache optimization completed")
            except Exception as e:
                self.logger.error(f"Error in cache optimization: {e}")
                await asyncio.sleep(300)

    async def _update_asset_cache(self):
        """Update asset cache"""
        try:
            assets_data = [asdict(asset) for asset in self.assets.values()]
            await self.manager.cache_set('cdn_assets', assets_data, ttl=86400)
        except Exception as e:
            self.logger.error(f"Error updating asset cache: {e}")

    async def _update_zone_cache(self):
        """Update zone cache"""
        try:
            zones_data = [asdict(zone) for zone in self.zones.values()]
            await self.manager.cache_set('cdn_zones', zones_data, ttl=86400)
        except Exception as e:
            self.logger.error(f"Error updating zone cache: {e}")

    async def get_asset_url(self, asset_id: str, provider: str = None) -> Optional[str]:
        """Get CDN URL for an asset"""
        try:
            if asset_id in self.assets:
                asset = self.assets[asset_id]
                if provider and asset.provider != provider:
                    # Try to find same asset on different provider
                    for other_asset in self.assets.values():
                        if (other_asset.checksum == asset.checksum and
                            other_asset.provider == provider):
                            return other_asset.url
                    return None
                return asset.url
            return None
        except Exception as e:
            self.logger.error(f"Error getting asset URL: {e}")
            return None

    async def list_assets(self, provider: str = None,
                         limit: int = 100,
                         offset: int = 0) -> Dict[str, Any]:
        """List CDN assets"""
        try:
            assets = list(self.assets.values())

            if provider:
                assets = [asset for asset in assets if asset.provider == provider]

            # Sort by creation date (newest first)
            assets.sort(key=lambda x: x.created_at, reverse=True)

            # Apply pagination
            total_count = len(assets)
            paginated_assets = assets[offset:offset + limit]

            return {
                'assets': [
                    {
                        'asset_id': asset.asset_id,
                        'url': asset.url,
                        'file_path': asset.file_path,
                        'file_size': asset.file_size,
                        'content_type': asset.content_type,
                        'provider': asset.provider,
                        'cache_ttl': asset.cache_ttl,
                        'created_at': asset.created_at.isoformat(),
                        'last_accessed': asset.last_accessed.isoformat() if asset.last_accessed else None,
                        'access_count': asset.access_count
                    }
                    for asset in paginated_assets
                ],
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }

        except Exception as e:
            return {'error': str(e), 'assets': []}

    async def delete_asset(self, asset_id: str) -> Dict[str, Any]:
        """Delete an asset from CDN"""
        try:
            if asset_id not in self.assets:
                return {'success': False, 'error': 'Asset not found'}

            asset = self.assets[asset_id]

            # Delete from provider
            if asset.provider == 'cloudflare' and self.cloudflare_client:
                result = await self._delete_from_cloudflare(asset_id)
            elif asset.provider == 'aws' and self.aws_client:
                result = await self._delete_from_aws(asset_id)
            elif asset.provider == 'fastly' and self.fastly_client:
                result = await self._delete_from_fastly(asset_id)
            else:
                return {'success': False, 'error': f'Provider {asset.provider} not available'}

            if result['success']:
                # Remove from local storage
                del self.assets[asset_id]
                await self._update_asset_cache()

            return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _delete_from_cloudflare(self, asset_id: str) -> Dict[str, Any]:
        """Delete asset from Cloudflare"""
        try:
            # Cloudflare deletion logic would go here
            return {'success': True, 'provider': 'cloudflare'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _delete_from_aws(self, asset_id: str) -> Dict[str, Any]:
        """Delete asset from AWS"""
        try:
            # AWS deletion logic would go here
            return {'success': True, 'provider': 'aws'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _delete_from_fastly(self, asset_id: str) -> Dict[str, Any]:
        """Delete asset from Fastly"""
        try:
            # Fastly deletion logic would go here
            return {'success': True, 'provider': 'fastly'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_status(self) -> IntegrationStatus:
        """Get integration status"""
        return self.status

    async def enable(self):
        """Enable the integration"""
        self.status = IntegrationStatus.ACTIVE
        self.logger.info("CDN Manager Integration enabled")

    async def disable(self):
        """Disable the integration"""
        self.status = IntegrationStatus.INACTIVE
        self.logger.info("CDN Manager Integration disabled")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'providers': {},
            'metrics': {
                'total_assets': len(self.assets),
                'total_zones': len(self.zones),
                'cache_hit_rate': self.cache_stats['cache_hit_rate'],
                'bandwidth_saved_gb': self.cache_stats['bandwidth_saved']
            }
        }

        # Check Cloudflare
        if self.cloudflare_client:
            try:
                # Test Cloudflare API
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'Authorization': f'Bearer {self.cloudflare_client["api_token"]}'
                    }
                    async with session.get(
                        f"{self.cloudflare_client['base_url']}/user/tokens/verify",
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            health_status['providers']['cloudflare'] = {'status': 'connected'}
                        else:
                            health_status['providers']['cloudflare'] = {'status': 'error'}
            except Exception as e:
                health_status['providers']['cloudflare'] = {'status': 'error', 'error': str(e)}

        # Check AWS
        if self.aws_client:
            health_status['providers']['aws'] = {'status': 'configured'}

        # Check Fastly
        if self.fastly_client:
            health_status['providers']['fastly'] = {'status': 'configured'}

        return health_status

    async def check_rate_limit(self):
        """Check rate limits"""
        # Rate limiting would be implemented here
        pass

    async def handle_webhook(self, event_type: str, data: Dict[str, Any]):
        """Handle webhook events"""
        if event_type == 'upload_asset':
            await self.upload_asset(
                file_path=data.get('file_path'),
                provider=data.get('provider', 'cloudflare'),
                cache_ttl=data.get('cache_ttl', 86400)
            )
        elif event_type == 'purge_asset':
            await self.purge_asset(
                asset_id=data.get('asset_id'),
                provider=data.get('provider')
            )

    async def shutdown(self):
        """Shutdown the integration"""
        self.logger.info("CDN Manager Integration shutdown")