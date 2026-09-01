"""
Management command to seed SelectorConfig entries for all social wavelets.
Run with: python manage.py seed_selector_configs
Use --force to overwrite existing entries.
"""

from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

from core.models import SelectorConfig
from core.signals import update_extension_selector_versions
from core.tasks import (
    SELECTOR_VERSION_PROPAGATION_DELAY_SECONDS,
    update_selector_bundle_version_task,
)

SELECTOR_CONFIGS = [
    {
        "family": "social",
        "provider": "x",
        "version": "1.7.5",
        "hostname_patterns": ["x.com", "twitter.com"],
        "selectors": {
            "tweet_article": ["article[data-testid='tweet']"],
            "status_link": ["a[href*='/status/']"],
            "tweet_text": ["[data-testid='tweetText']"],
            "retweet_btn": ["[data-testid='retweet']"],
            "display_name": ["[data-testid='User-Name'] span"],
            "timestamp": ["time"],
            "metrics_group": ["[role='group']"],
            "verified_badge": [
                "[data-testid='User-Name'] svg[data-testid='icon-verified']"
            ],
            "video_player": ["[data-testid='videoPlayer']", "video"],
            "photo": ["[data-testid='tweetPhoto']"],
            "promoted_indicator": ["[data-testid='promotedIndicator']"],
        },
    },
    {
        "family": "social",
        "provider": "tiktok",
        "version": "1.7.5",
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
            "content_flex": ["div[class*='DivContentFlexLayout']"],
        },
    },
    {
        "family": "social",
        "provider": "youtube_shorts",
        "version": "1.7.5",
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
        "version": "1.7.5",
        "hostname_patterns": ["youtube.com"],
        "selectors": {
            "feed_item": ["ytd-rich-item-renderer, ytd-video-renderer"],
            "video_link": ["a[href*='/watch?v=']"],
            "title": ["h3 a span, .ytLockupMetadataViewModelTitle span"],
            "channel_link": ["a[href^='/@']"],
            "metadata": ["yt-content-metadata-view-model"],
            "duration": [
                "badge-shape .ytBadgeShapeText, "
                ".ytThumbnailBottomOverlayViewModelBadge .ytBadgeShapeText"
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
        "version": "1.7.5",
        "hostname_patterns": ["youtube.com"],
        "selectors": {
            "watch_flexy": ["ytd-watch-flexy"],
            "title": ["ytd-watch-metadata h1 yt-formatted-string"],
            "title_alt": [
                "ytd-video-primary-info-renderer h1.title yt-formatted-string"
            ],
            "channel_link": [
                "ytd-video-owner-renderer a[href^='/@'], "
                "ytd-channel-name a[href^='/@']"
            ],
            "channel_name": [
                "ytd-channel-name #text, "
                "ytd-video-owner-renderer #text, "
                "#upload-info #channel-name #text"
            ],
            "view_count": [
                "ytd-video-view-count-renderer .view-count, "
                "ytd-watch-info-text #view-count"
            ],
            "upload_date": [
                "ytd-video-primary-info-renderer #info-strings "
                "yt-formatted-string, ytd-watch-info-text "
                "#date-text yt-formatted-string"
            ],
            "like_button": [
                "like-button-view-model button[aria-label*='like' i], "
                "ytd-menu-renderer like-button-view-model button"
            ],
            "comments_header": [
                "ytd-comments-header-renderer #count, "
                "ytd-engagement-panel-title-header-renderer #title"
            ],
            "description": [
                "ytd-text-inline-expander #snippet-text, "
                "ytd-expandable-video-description-body-renderer "
                "ytd-text-inline-expander #snippet-text"
            ],
        },
    },
    {
        "family": "social",
        "provider": "instagram",
        "version": "1.7.5",
        "hostname_patterns": ["instagram.com"],
        "selectors": {
            "post_article": ["article"],
            "post_link": ["a[href*='/p/']"],
            "ad_marker": ["span.x1fhwpqd.x132q4wb"],
            "author_handle": ["span._ap3a._aacw"],
            "timestamp": ["time[datetime]"],
            "caption": ["[data-testid='caption'] span, span._ap3a._aacu._aad7"],
            "verified_badge": ["svg[aria-label='Verified']"],
            "carousel_list": ["._aagu ul"],
        },
    },
    {
        "family": "social",
        "provider": "facebook",
        "version": "1.7.5",
        "hostname_patterns": ["facebook.com"],
        "selectors": {
            "article": ["div[role='article']"],
            "profile_link": ["[data-ad-rendering-role='profile_name'] a"],
            "story_message": [
                "[data-ad-rendering-role='story_message']",
                "blockquote",
            ],
            "time_link": [
                "a[href*='/posts/']",
                "a[href*='/watch/']",
                "a[href*='?v=']",
                "a[href*='/photo/']",
            ],
            "sponsored_marker": [
                "a[aria-label='Publicidad']",
                "a[aria-label='Sponsored']",
                "a[aria-label='Patrocinado']",
                "a[aria-label='Gesponsert']",
                "a[aria-label='Sponsorisé']",
            ],
            "ads_link": ["a[href*='/ads/']"],
            "ad_role_marker": ["[data-ad-rendering-role='cta-']"],
            "public_indicator": [
                "svg[title*='Público']",
                "svg[title*='Public']",
                "svg[title*='Öffentlich']",
                "svg[title*='Publiek']",
            ],
            "like_button": [
                "div[aria-label='Me gusta']",
                "div[aria-label='Like']",
                "div[aria-label='Gefällt mir']",
                "div[aria-label=\"J'aime\"]",
                "div[aria-label='Curtir']",
                "[data-ad-rendering-role='like_button']",
            ],
            "comment_button": [
                "div[aria-label='Dejar un comentario']",
                "div[aria-label='Leave a comment']",
                "div[aria-label='Comment']",
                "div[aria-label='Kommentar hinterlassen']",
                "div[aria-label='Laisser un commentaire']",
                "div[aria-label='Comentar']",
                "[data-ad-rendering-role='comment_button']",
            ],
            "share_button": [
                "div[aria-label^='Envía']",
                "div[aria-label^='Enviar']",
                "div[aria-label^='Compartir']",
                "div[aria-label^='Share']",
                "div[aria-label^='Teilen']",
                "div[aria-label^='Sende']",
                "div[aria-label^='Partager']",
                "div[aria-label^='Compartilhar']",
                "[data-ad-rendering-role='share_button']",
            ],
        },
    },
    {
        "family": "social",
        "provider": "facebook_reels",
        "version": "1.7.5",
        "hostname_patterns": ["facebook.com"],
        "selectors": {
            "reel_card": ["a[href*='/reel/'][aria-label]"],
            "thumbnail": ["img[src*='fbcdn']"],
        },
    },
    {
        "family": "social",
        "provider": "linkedin",
        "version": "1.7.5",
        "hostname_patterns": ["linkedin.com"],
        "selectors": {
            "listitem": ["div[role='listitem']"],
            "post_text": ["[data-testid='expandable-text-box']"],
            "visibility_icon": [
                "svg#globe-americas-small",
                "svg[aria-label^='Visibility:']",
            ],
            "control_menu_btn": [
                "button[aria-label*='post by']",
                "button[aria-label*='Beitrag von']",
            ],
            "reaction_button": [
                "button[aria-label*='Reaction button']",
                "button[aria-label*='Reaktionsbuttons']",
            ],
            "comment_button": [
                "button[aria-label='Comment']",
                "button[aria-label='Kommentieren']",
            ],
            "repost_button": [
                "button[aria-label='Repost']",
                "button[aria-label='Reposten']",
            ],
            "profile_link": ["a[href*='/in/']"],
            "group_link": ["a[href*='/groups/']"],
            "media_image": [
                "img[alt^='View image']",
                "img[src*='feedshare']",
            ],
            "external_link": ["a[target='_blank'][href^='http']"],
            "author_link": [
                "a[href*='/in/']",
                "a[href*='/company/']",
                "a[href*='/groups/']",
            ],
        },
    },
    {
        "family": "social",
        "provider": "reddit",
        "version": "1.7.5",
        "hostname_patterns": ["reddit.com"],
        "selectors": {
            "shreddit_post": ["shreddit-post"],
        },
    },
    {
        "family": "social",
        "provider": "twitch_feed",
        "version": "1.7.5",
        "hostname_patterns": ["twitch.tv"],
        "selectors": {
            "stream_card": ["[data-test-selector='shelf-card-selector']"],
            "stream_title": ["[data-test-selector='StreamTitle'] h4"],
            "channel_link": ["[data-test-selector='TitleAndChannel']"],
            "display_name": ["[data-a-target='preview-card-channel-link'] p[title]"],
            "game_link": ["[data-test-selector='GameLink']"],
            "viewer_count": [".tw-media-card-stat"],
            "tags": [".tw-tag"],
            "verified": [
                "a[data-test-selector='TitleAndChannel'][aria-label*='(Verified)']"
            ],
            "live_badge": [".tw-channel-status-text-indicator"],
            "thumbnail": ["img.tw-image"],
        },
    },
    {
        "family": "social",
        "provider": "twitch_stream",
        "version": "1.7.5",
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
        "version": "1.7.5",
        "hostname_patterns": ["threads.com", "threads.net"],
        "selectors": {
            "threads_post": ["[data-pressable-container='true']"],
            "post_link": ["a[href*='/post/']"],
            "author_link": ["a[href^='/@']"],
            "verified_badge": [
                "svg[aria-label='Verified']",
                "svg[aria-label='Verificado']",
            ],
            "ufi_group": [
                "[role='group']",
                "div[class*='ufi']",
                "div[aria-label*='like']",
                "div[aria-label*='repost']",
            ],
            "timestamp": ["time[datetime]"],
        },
    },
    {
        "family": "llm",
        "provider": "chatgpt",
        "version": "1.7.5",
        "hostname_patterns": ["chatgpt.com", "chat.openai.com"],
        "selectors": {
            "role_attribute": ["data-message-author-role"],
            "content": [".whitespace-pre-wrap"],
            "message_id_attribute": ["data-message-id"],
            "message_container": ["[data-message-author-role]"],
        },
    },
    {
        "family": "llm",
        "provider": "claude",
        "version": "1.7.5",
        "hostname_patterns": ["claude.ai"],
        "selectors": {
            "user_content": [".whitespace-pre-wrap"],
            "assistant_content": [".font-claude-response-body"],
            "user_container": ["[data-testid='user-message']"],
            "streaming_attribute": ["data-is-streaming"],
        },
    },
    {
        "family": "llm",
        "provider": "deepseek",
        "version": "1.7.5",
        "hostname_patterns": ["deepseek.com"],
        "selectors": {
            "assistant_marker": [":scope > .ds-markdown"],
            "content_exclude": [".ds-think-content"],
            "message_container": [".ds-message"],
            "stable_id_closest": ["[data-virtual-list-item-key]"],
            "stable_id_attribute": ["data-virtual-list-item-key"],
        },
    },
    {
        "family": "llm",
        "provider": "gemini",
        "version": "1.7.5",
        "hostname_patterns": ["gemini.google.com"],
        "selectors": {
            "user_content": ["p.query-text-line"],
            "assistant_content": [".markdown.markdown-main-panel"],
            "streaming_element": [".markdown.markdown-main-panel"],
            "user_container": ["user-query"],
            "assistant_container": ["model-response"],
            "stable_id_closest": [".conversation-container"],
            "streaming_attribute": ["aria-busy"],
        },
    },
]


class Command(BaseCommand):
    """Seed SelectorConfig entries for all social wavelets."""

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
        bundle_version = SELECTOR_CONFIGS[0]["version"]

        post_save.disconnect(update_extension_selector_versions, sender=SelectorConfig)

        try:
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
        finally:
            post_save.connect(update_extension_selector_versions, sender=SelectorConfig)

        if created_count or updated_count:
            task = update_selector_bundle_version_task.apply_async(  # type: ignore
                args=(bundle_version,),
                countdown=SELECTOR_VERSION_PROPAGATION_DELAY_SECONDS,
                description=f"Update selector bundle version to {bundle_version}",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "  SCHEDULED selector bundle propagation "
                    f"to {bundle_version}. Task ID: {task.id}"
                )
            )

        self.stdout.write(
            f"\nDone - {created_count} created, {updated_count} updated, {skipped_count} skipped."
        )
