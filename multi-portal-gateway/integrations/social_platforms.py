#!/usr/bin/env python3
"""
Social Platforms Integration
Connects with Discord, Twitter/X, Reddit, and other social media platforms
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import discord
import tweepy
import praw
from .integration_manager import IntegrationStatus

@dataclass
class SocialPost:
    platform: str
    content: str
    media_urls: List[str]
    hashtags: List[str]
    mentions: List[str]
    scheduled_time: Optional[datetime]
    engagement_stats: Dict[str, int]

class SocialPlatformsIntegration:
    """Integration with social media platforms"""

    def __init__(self, integration_manager):
        self.manager = integration_manager
        self.logger = logging.getLogger(__name__)
        self.config = {}
        self.status = IntegrationStatus.INACTIVE

        # Platform clients
        self.discord_client = None
        self.twitter_client = None
        self.reddit_client = None

        # Rate limiters
        self.rate_limiters = {}

    async def initialize(self):
        """Initialize the social platforms integration"""
        self.logger.info("Initializing Social Platforms Integration")

        # Initialize Discord bot
        await self._initialize_discord()

        # Initialize Twitter client
        await self._initialize_twitter()

        # Initialize Reddit client
        await self._initialize_reddit()

        # Initialize rate limiters
        await self._initialize_rate_limiters()

        self.status = IntegrationStatus.ACTIVE

    async def _initialize_discord(self):
        """Initialize Discord bot client"""
        try:
            discord_token = self.config.get('api_keys', {}).get('discord_bot_token')
            if discord_token:
                intents = discord.Intents.default()
                intents.message_content = True
                intents.guilds = True

                self.discord_client = discord.Client(intents=intents)

                # Setup event handlers
                @self.discord_client.event
                async def on_ready():
                    self.logger.info(f"Discord bot logged in as {self.discord_client.user}")

                @self.discord_client.event
                async def on_message(message):
                    if not message.author.bot:
                        await self._handle_discord_message(message)

                # Start bot in background
                asyncio.create_task(self.discord_client.start(discord_token))
                self.logger.info("Discord bot initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Discord: {e}")

    async def _initialize_twitter(self):
        """Initialize Twitter/X client"""
        try:
            api_key = self.config.get('api_keys', {}).get('twitter_api_key')
            api_secret = self.config.get('api_keys', {}).get('twitter_api_secret')
            access_token = self.config.get('api_keys', {}).get('twitter_access_token')
            access_token_secret = self.config.get('api_keys', {}).get('twitter_access_token_secret')

            if all([api_key, api_secret, access_token, access_token_secret]):
                self.twitter_client = tweepy.Client(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret
                )
                self.logger.info("Twitter client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter: {e}")

    async def _initialize_reddit(self):
        """Initialize Reddit client"""
        try:
            client_id = self.config.get('api_keys', {}).get('reddit_client_id')
            client_secret = self.config.get('api_keys', {}).get('reddit_client_secret')
            user_agent = self.config.get('reddit_user_agent', 'DMLogn8n Bot v1.0')

            if client_id and client_secret:
                self.reddit_client = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent,
                    read_only=True
                )
                self.logger.info("Reddit client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit: {e}")

    async def _initialize_rate_limiters(self):
        """Initialize rate limiters for each platform"""
        rate_limits = self.config.get('rate_limits', {})

        for platform, limit in rate_limits.items():
            self.rate_limiters[platform] = self.manager.RateLimiter(limit)

    async def _handle_discord_message(self, message):
        """Handle incoming Discord messages"""
        try:
            # Process message content
            content = message.content.lower()

            # Check for commands
            if content.startswith('!dmlog'):
                await self._handle_discord_command(message)

            # Log message for analytics
            await self._log_discord_activity(message)

        except Exception as e:
            self.logger.error(f"Error handling Discord message: {e}")

    async def _handle_discord_command(self, message):
        """Handle Discord bot commands"""
        try:
            parts = message.content.split()
            command = parts[1] if len(parts) > 1 else 'help'

            if command == 'status':
                await message.reply("DMLogn8n systems operational ✅")
            elif command == 'help':
                help_text = """
**DMLogn8n Bot Commands:**
• `!dmlog status` - Check system status
• `!dmlog share <content>` - Share content to social platforms
• `!dmlog analytics` - Get community analytics
• `!dmlog events` - List upcoming events
                """
                await message.reply(help_text)
            elif command == 'share' and len(parts) > 2:
                content = ' '.join(parts[2:])
                result = await self.cross_platform_post(content)
                await message.reply(f"Shared to platforms: {', '.join(result.keys())}")

        except Exception as e:
            self.logger.error(f"Error handling Discord command: {e}")
            await message.reply("Sorry, there was an error processing your command.")

    async def _log_discord_activity(self, message):
        """Log Discord activity for analytics"""
        try:
            activity_data = {
                'platform': 'discord',
                'user_id': str(message.author.id),
                'username': message.author.name,
                'guild_id': str(message.guild.id) if message.guild else None,
                'channel_id': str(message.channel.id),
                'content_length': len(message.content),
                'timestamp': message.created_at.isoformat(),
                'has_attachments': len(message.attachments) > 0
            }

            # Send to analytics
            await self.manager.execute_webhook('analytics_services', 'social_activity', activity_data)

        except Exception as e:
            self.logger.error(f"Error logging Discord activity: {e}")

    async def cross_platform_post(self, content: str,
                                platforms: List[str] = None,
                                media_urls: List[str] = None,
                                hashtags: List[str] = None) -> Dict[str, Any]:
        """Post content across multiple social platforms"""
        if platforms is None:
            platforms = ['discord', 'twitter', 'reddit']

        results = {}

        for platform in platforms:
            try:
                if platform == 'discord' and self.discord_client:
                    result = await self._post_to_discord(content, media_urls)
                    results['discord'] = result
                elif platform == 'twitter' and self.twitter_client:
                    result = await self._post_to_twitter(content, hashtags, media_urls)
                    results['twitter'] = result
                elif platform == 'reddit' and self.reddit_client:
                    result = await self._post_to_reddit(content)
                    results['reddit'] = result

            except Exception as e:
                self.logger.error(f"Failed to post to {platform}: {e}")
                results[platform] = {'success': False, 'error': str(e)}

        return results

    async def _post_to_discord(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post message to Discord channels"""
        try:
            await self.rate_limiters['discord'].acquire()

            # Get configured channels
            channels = self.config.get('discord_channels', [])
            posted_channels = []

            for channel_id in channels:
                channel = self.discord_client.get_channel(int(channel_id))
                if channel:
                    if media_urls:
                        await channel.send(content, files=[discord.File(url) for url in media_urls])
                    else:
                        await channel.send(content)
                    posted_channels.append(channel_id)

            return {
                'success': True,
                'posted_channels': posted_channels,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _post_to_twitter(self, content: str, hashtags: List[str] = None,
                             media_urls: List[str] = None) -> Dict[str, Any]:
        """Post tweet to Twitter/X"""
        try:
            await self.rate_limiters['twitter'].acquire()

            # Format content with hashtags
            if hashtags:
                content += ' ' + ' '.join([f"#{tag}" for tag in hashtags])

            # Handle Twitter character limit
            if len(content) > 280:
                content = content[:277] + '...'

            # Upload media if provided
            media_ids = []
            if media_urls:
                # Twitter media upload would go here
                pass

            response = self.twitter_client.create_tweet(
                text=content,
                media_ids=media_ids if media_ids else None
            )

            return {
                'success': True,
                'tweet_id': response.data['id'],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _post_to_reddit(self, content: str, subreddit: str = 'r/DMLogn8n') -> Dict[str, Any]:
        """Post to Reddit"""
        try:
            await self.rate_limiters['reddit'].acquire()

            # Split title and content
            lines = content.split('\n', 1)
            title = lines[0][:300]  # Reddit title limit
            body = lines[1] if len(lines) > 1 else ''

            submission = self.reddit_client.subreddit(subreddit).submit(
                title=title,
                selftext=body,
                send_replies=True
            )

            return {
                'success': True,
                'post_id': submission.id,
                'url': f"https://reddit.com{submission.permalink}",
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_platform_analytics(self, platform: str,
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> Dict[str, Any]:
        """Get analytics for specific platform"""
        try:
            if platform == 'twitter' and self.twitter_client:
                return await self._get_twitter_analytics(start_date, end_date)
            elif platform == 'reddit' and self.reddit_client:
                return await self._get_reddit_analytics(start_date, end_date)
            elif platform == 'discord':
                return await self._get_discord_analytics(start_date, end_date)
            else:
                return {'error': f'Analytics not available for {platform}'}

        except Exception as e:
            return {'error': str(e)}

    async def _get_twitter_analytics(self, start_date: datetime,
                                   end_date: datetime) -> Dict[str, Any]:
        """Get Twitter analytics"""
        try:
            # Get recent tweets
            tweets = self.twitter_client.get_users_tweets(
                me=True,
                tweet_fields=['public_metrics', 'created_at'],
                max_results=100
            )

            total_engagement = 0
            total_impressions = 0
            tweet_count = 0

            if tweets.data:
                for tweet in tweets.data:
                    metrics = tweet.public_metrics
                    total_engagement += (
                        metrics.get('like_count', 0) +
                        metrics.get('retweet_count', 0) +
                        metrics.get('reply_count', 0) +
                        metrics.get('quote_count', 0)
                    )
                    total_impressions += metrics.get('impression_count', 0)
                    tweet_count += 1

            return {
                'platform': 'twitter',
                'tweet_count': tweet_count,
                'total_engagement': total_engagement,
                'total_impressions': total_impressions,
                'engagement_rate': (total_engagement / total_impressions * 100) if total_impressions > 0 else 0,
                'period': f"{start_date} to {end_date}" if start_date and end_date else "Last 100 tweets"
            }

        except Exception as e:
            return {'error': str(e)}

    async def _get_reddit_analytics(self, start_date: datetime,
                                  end_date: datetime) -> Dict[str, Any]:
        """Get Reddit analytics"""
        try:
            # Get user's posts and comments
            user = self.reddit_client.user.me()

            posts = []
            comments = []

            # Get recent submissions
            for submission in user.submissions.new(limit=100):
                posts.append({
                    'id': submission.id,
                    'title': submission.title,
                    'score': submission.score,
                    'upvote_ratio': submission.upvote_ratio,
                    'num_comments': submission.num_comments,
                    'created_at': submission.created_utc
                })

            # Get recent comments
            for comment in user.comments.new(limit=100):
                comments.append({
                    'id': comment.id,
                    'body': comment.body[:100] + '...' if len(comment.body) > 100 else comment.body,
                    'score': comment.score,
                    'created_at': comment.created_utc
                })

            total_post_karma = sum(post['score'] for post in posts)
            total_comment_karma = sum(comment['score'] for comment in comments)

            return {
                'platform': 'reddit',
                'post_count': len(posts),
                'comment_count': len(comments),
                'total_post_karma': total_post_karma,
                'total_comment_karma': total_comment_karma,
                'average_post_score': total_post_karma / len(posts) if posts else 0,
                'period': f"{start_date} to {end_date}" if start_date and end_date else "Last 100 posts/comments"
            }

        except Exception as e:
            return {'error': str(e)}

    async def _get_discord_analytics(self, start_date: datetime,
                                   end_date: datetime) -> Dict[str, Any]:
        """Get Discord analytics"""
        try:
            # Get server statistics
            guild_count = len(self.discord_client.guilds)
            total_members = sum(guild.member_count for guild in self.discord_client.guilds)

            # Get activity from cache/database
            activity_data = await self.manager.cache_get('discord_activity_analytics')

            if not activity_data:
                activity_data = {
                    'messages_sent': 0,
                    'commands_used': 0,
                    'active_users': set(),
                    'popular_channels': {}
                }

            return {
                'platform': 'discord',
                'server_count': guild_count,
                'total_members': total_members,
                'messages_sent': activity_data.get('messages_sent', 0),
                'commands_used': activity_data.get('commands_used', 0),
                'active_users': len(activity_data.get('active_users', [])),
                'period': f"{start_date} to {end_date}" if start_date and end_date else "All time"
            }

        except Exception as e:
            return {'error': str(e)}

    async def schedule_post(self, post: SocialPost) -> Dict[str, Any]:
        """Schedule a social media post"""
        try:
            # Store scheduled post
            scheduled_posts = await self.manager.cache_get('scheduled_posts') or []

            post_data = {
                'id': len(scheduled_posts) + 1,
                'platform': post.platform,
                'content': post.content,
                'media_urls': post.media_urls,
                'hashtags': post.hashtags,
                'mentions': post.mentions,
                'scheduled_time': post.scheduled_time.isoformat(),
                'status': 'scheduled'
            }

            scheduled_posts.append(post_data)
            await self.manager.cache_set('scheduled_posts', scheduled_posts, ttl=86400)

            # Schedule execution
            if post.scheduled_time:
                delay = (post.scheduled_time - datetime.now()).total_seconds()
                if delay > 0:
                    asyncio.create_task(self._execute_scheduled_post(post_data, delay))

            return {
                'success': True,
                'post_id': post_data['id'],
                'scheduled_time': post.scheduled_time.isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _execute_scheduled_post(self, post_data: Dict[str, Any], delay: float):
        """Execute a scheduled post"""
        await asyncio.sleep(delay)

        try:
            await self.cross_platform_post(
                content=post_data['content'],
                platforms=[post_data['platform']],
                media_urls=post_data['media_urls'],
                hashtags=post_data['hashtags']
            )

            # Update post status
            post_data['status'] = 'posted'
            post_data['posted_time'] = datetime.now().isoformat()

            self.logger.info(f"Executed scheduled post {post_data['id']}")

        except Exception as e:
            self.logger.error(f"Failed to execute scheduled post {post_data['id']}: {e}")
            post_data['status'] = 'failed'
            post_data['error'] = str(e)

    async def monitor_social_mentions(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Monitor social media for mentions"""
        mentions = []

        # Monitor Twitter
        if self.twitter_client:
            try:
                tweets = self.twitter_client.search_recent_tweets(
                    query=' OR '.join(keywords),
                    tweet_fields=['created_at', 'author_id'],
                    max_results=10
                )

                if tweets.data:
                    for tweet in tweets.data:
                        mentions.append({
                            'platform': 'twitter',
                            'content': tweet.text,
                            'author_id': tweet.author_id,
                            'created_at': tweet.created_at,
                            'url': f"https://twitter.com/user/status/{tweet.id}"
                        })
            except Exception as e:
                self.logger.error(f"Error monitoring Twitter mentions: {e}")

        # Monitor Reddit
        if self.reddit_client:
            try:
                for keyword in keywords:
                    for submission in self.reddit_client.subreddit('all').search(keyword, limit=5):
                        mentions.append({
                            'platform': 'reddit',
                            'content': submission.title,
                            'author': str(submission.author),
                            'created_at': datetime.fromtimestamp(submission.created_utc),
                            'url': f"https://reddit.com{submission.permalink}"
                        })
            except Exception as e:
                self.logger.error(f"Error monitoring Reddit mentions: {e}")

        return mentions

    async def get_status(self) -> IntegrationStatus:
        """Get integration status"""
        return self.status

    async def enable(self):
        """Enable the integration"""
        self.status = IntegrationStatus.ACTIVE
        self.logger.info("Social Platforms Integration enabled")

    async def disable(self):
        """Disable the integration"""
        self.status = IntegrationStatus.INACTIVE
        self.logger.info("Social Platforms Integration disabled")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'platforms': {}
        }

        # Check Discord
        if self.discord_client:
            try:
                health_status['platforms']['discord'] = {
                    'status': 'connected' if not self.discord_client.is_closed() else 'disconnected',
                    'guilds': len(self.discord_client.guilds)
                }
            except Exception as e:
                health_status['platforms']['discord'] = {'status': 'error', 'error': str(e)}

        # Check Twitter
        if self.twitter_client:
            try:
                # Test Twitter API
                me = self.twitter_client.get_me()
                health_status['platforms']['twitter'] = {
                    'status': 'connected' if me else 'disconnected'
                }
            except Exception as e:
                health_status['platforms']['twitter'] = {'status': 'error', 'error': str(e)}

        # Check Reddit
        if self.reddit_client:
            try:
                # Test Reddit API
                me = self.reddit_client.user.me()
                health_status['platforms']['reddit'] = {
                    'status': 'connected' if me else 'disconnected'
                }
            except Exception as e:
                health_status['platforms']['reddit'] = {'status': 'error', 'error': str(e)}

        # Check if any platform has errors
        if any(platform.get('status') == 'error' for platform in health_status['platforms'].values()):
            health_status['status'] = 'degraded'

        return health_status

    async def check_rate_limit(self):
        """Check rate limits"""
        # Rate limiting is handled by individual platform methods
        pass

    async def handle_webhook(self, event_type: str, data: Dict[str, Any]):
        """Handle webhook events"""
        if event_type == 'share_content':
            await self.cross_platform_post(
                content=data.get('content', ''),
                platforms=data.get('platforms', []),
                media_urls=data.get('media_urls', []),
                hashtags=data.get('hashtags', [])
            )
        elif event_type == 'schedule_post':
            post = SocialPost(
                platform=data.get('platform', 'twitter'),
                content=data.get('content', ''),
                media_urls=data.get('media_urls', []),
                hashtags=data.get('hashtags', []),
                mentions=data.get('mentions', []),
                scheduled_time=datetime.fromisoformat(data.get('scheduled_time'))
            )
            await self.schedule_post(post)

    async def shutdown(self):
        """Shutdown the integration"""
        if self.discord_client:
            await self.discord_client.close()
        self.logger.info("Social Platforms Integration shutdown")