"""
Management command to seed SelectorConfig entries for all social wavelets.
Run with: python manage.py seed_selector_configs
Use --force to overwrite existing entries.
"""

from core.models import SelectorConfig
from django.core.management.base import BaseCommand

SELECTOR_CONFIGS = [
    {
        "family": "social",
        "provider": "x",
        "version": "1.0.0",
        "hostname_patterns": ["x.com", "twitter.com"],
        "selectors": {
            "tweet_article": ["article[data-testid='tweet']"],
            "status_link": ["a[href*='/status/']"],
            "tweet_text": ["[data-testid='tweetText']"],
            "display_name": ["[data-testid='User-Name'] span"],
            "timestamp": ["time"],
            "metrics_group": ["[role='group']"],
        },
    },
    {
        "family": "social",
        "provider": "tiktok",
        "version": "1.0.0",
        "hostname_patterns": ["tiktok.com"],
        "selectors": {
            "player_wrapper": ["[id^='xgwrapper-']"],
            "author_avatar": ["[data-e2e='video-author-avatar']"],
            "display_name": ["[data-e2e='video-author-avatar'] ~ * p"],
            "verified_check": [
                "[data-e2e='video-author-avatar'] ~ * path[fill='#20D5EC']"
            ],
            "caption_span": ["[data-e2e^='desc-span']"],
            "like_count": ["[data-e2e='like-count']"],
            "comment_count": ["[data-e2e='comment-count']"],
            "share_count": ["[data-e2e='share-count']"],
            "favorites_button": ["button[aria-label*='Favorites']"],
            "music_link": ["[data-e2e='video-music']"],
            "feed_section": ["[data-e2e='feed-video']"],
            "content_flex": [
                "div[class*='DivContentFlexLayout']"
            ],  # used by TikTokWavelet + TikTokPlayedWavelet
        },
    },
    {
        "family": "social",
        "provider": "youtube_shorts",
        "version": "1.0.0",
        "hostname_patterns": ["youtube.com"],
        "selectors": {
            "reel_overlay": ["ytd-reel-player-overlay-renderer"],
            "channel_link": ["a[href^='/@']"],
            "video_title": ["yt-shorts-video-title-view-model h2"],
            "like_button": ["like-button-view-model button[aria-label]"],
            "comment_button": ["button[aria-label*='comment' i]"],
        },
    },
    {
        "family": "social",
        "provider": "youtube_feed",
        "version": "1.0.0",
        "hostname_patterns": ["youtube.com"],
        "selectors": {
            "feed_item": ["ytd-rich-item-renderer, ytd-video-renderer"],
            "video_link": ["a[href*='/watch?v=']"],
            "title": ["h3 a span, .ytLockupMetadataViewModelTitle span"],
            "channel_link": ["a[href^='/@']"],
            "metadata": ["yt-content-metadata-view-model"],
            "duration": [
                "badge-shape .ytBadgeShapeText, .ytThumbnailBottomOverlayViewModelBadge .ytBadgeShapeText"
            ],
            "thumbnail": ["img[src*='ytimg.com']"],
            "live_badge": [".ytSpecAvatarShapeLiveBadge, [aria-label*='live' i]"],
            "ad_badge": [
                "yt-ad-slot-renderer, [aria-label*='sponsored' i], [aria-label*='ad' i]"
            ],
        },
    },
    {
        "family": "social",
        "provider": "youtube_watch",
        "version": "1.0.0",
        "hostname_patterns": ["youtube.com"],
        "selectors": {
            "watch_flexy": ["ytd-watch-flexy"],
            "title": ["ytd-watch-metadata h1 yt-formatted-string"],
            "title_alt": [
                "ytd-video-primary-info-renderer h1.title yt-formatted-string"
            ],
            "channel_link": [
                "ytd-video-owner-renderer a[href^='/@'], ytd-channel-name a[href^='/@']"
            ],
            "view_count": [
                "ytd-video-view-count-renderer .view-count, ytd-watch-info-text #view-count"
            ],
            "upload_date": [
                "ytd-video-primary-info-renderer #info-strings yt-formatted-string, ytd-watch-info-text #date-text yt-formatted-string"
            ],
            "like_button": [
                "like-button-view-model button[aria-label*='like' i], ytd-menu-renderer like-button-view-model button"
            ],
            "comments_header": [
                "ytd-comments-header-renderer #count, ytd-engagement-panel-title-header-renderer #title"
            ],
            "description": [
                "ytd-text-inline-expander #snippet-text, ytd-expandable-video-description-body-renderer ytd-text-inline-expander #snippet-text"
            ],
        },
    },
    {
        "family": "social",
        "provider": "instagram",
        "version": "1.0.0",
        "hostname_patterns": ["instagram.com"],
        "selectors": {
            "post_article": ["article"],
            "post_link": ["a[href*='/p/']"],
            "ad_marker": ["span.x1fhwpqd.x132q4wb"],
            "author_handle": ["span._ap3a._aacw"],
            "timestamp": ["time[datetime]"],
            "caption": ["[data-testid='caption'] span, span._ap3a._aacu._aad7"],
            "carousel_list": ["._aagu ul"],
        },
    },
    {
        "family": "social",
        "provider": "facebook",
        "version": "1.0.0",
        "hostname_patterns": ["facebook.com"],
        "selectors": {
            "article": ["div[role='article']"],
            "ad_marker": ["a[aria-label='Publicidad']"],
            "profile_link": ["[data-ad-rendering-role='profile_name'] a"],
            "time_link": ["a[href*='/posts/']"],
            "story_message": ["[data-ad-rendering-role='story_message']"],
            "like_button": ["div[aria-label='Me gusta'], div[aria-label='Like']"],
            "comment_button": [
                "div[aria-label='Dejar un comentario'], div[aria-label='Comment']"
            ],
            "share_button": [
                "div[aria-label^='Envía'], div[aria-label^='Enviar'], div[aria-label^='Compartir'], div[aria-label^='Share']"
            ],
        },
    },
    {
        "family": "social",
        "provider": "linkedin",
        "version": "1.0.0",
        "hostname_patterns": ["linkedin.com"],
        "selectors": {
            "listitem": ["div[role='listitem']"],
            "post_text": ["[data-testid='expandable-text-box']"],
        },
    },
    {
        "family": "social",
        "provider": "reddit",
        "version": "1.0.0",
        "hostname_patterns": ["reddit.com"],
        "selectors": {
            "shreddit_post": ["shreddit-post"],
        },
    },
    {
        "family": "social",
        "provider": "twitch_feed",
        "version": "1.0.0",
        "hostname_patterns": ["twitch.tv"],
        "selectors": {
            "stream_card": ["[data-test-selector='shelf-card-selector']"],
            "stream_title": ["[data-test-selector='StreamTitle'] h4"],
            "channel_link": ["[data-test-selector='TitleAndChannel']"],
            "display_name": ["[data-a-target='preview-card-channel-link'] p[title]"],
            "game_link": ["[data-test-selector='GameLink']"],
            "viewer_count": [".tw-media-card-stat"],
            "tags": [".tw-tag"],
            "verified": ["svg[title='Verified']"],
            "live_badge": [".tw-channel-status-text-indicator"],
            "thumbnail": ["img.tw-image"],
        },
    },
    {
        "family": "social",
        "provider": "twitch_stream",
        "version": "1.0.0",
        "hostname_patterns": ["twitch.tv"],
        "selectors": {
            "stream_info": ["#live-channel-stream-information"],
            "stream_title": ["p[data-a-target='stream-title']"],
            "display_name": ["h1.tw-title"],
            "game_link": ["a[data-a-target='stream-game-link']"],
            "viewer_count": ["strong[data-a-target='animated-channel-viewers-count']"],
            "duration": [".live-time span"],
            "tags": [".tw-tag"],
            "verified": ["svg[aria-label='Verified Partner']"],
            "live_badge": [".tw-channel-status-text-indicator"],
        },
    },
    {
        "family": "social",
        "provider": "threads",
        "version": "1.0.0",
        "hostname_patterns": ["threads.com", "threads.net"],
        "selectors": {
            "threads_post": ["[data-pressable-container='true']"],
        },
    },
]


class Command(BaseCommand):
    help = "Seed SelectorConfig entries for all social wavelets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing entries.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for config in SELECTOR_CONFIGS:
            provider = config["provider"]
            exists = SelectorConfig.objects.filter(provider=provider).exists()

            if exists and not force:
                self.stdout.write(
                    f"  SKIP     {provider} (already exists, use --force to overwrite)"
                )
                skipped_count += 1
                continue

            _, created = SelectorConfig.objects.update_or_create(
                provider=provider,
                defaults={k: v for k, v in config.items() if k != "provider"},
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  CREATED  {provider}"))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f"  UPDATED  {provider}"))
                updated_count += 1

        self.stdout.write(
            f"\nDone — {created_count} created, {updated_count} updated, {skipped_count} skipped."
        )
