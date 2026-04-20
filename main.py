import re
import hashlib
import html
import secrets
import string
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from typing import Optional, List

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mediumpremium")

app = FastAPI(title="MediumPremium", version="2.0.0")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ── Constants ────────────────────────────────────────────────────────────────

TIMEOUT = 20

VALID_ID_CHARS = set(string.ascii_letters + string.digits)

KNOWN_MEDIUM_DOMAINS = (
    "medium.com", "towardsdatascience.com", "hackernoon.com",
    "betterprogramming.pub", "levelup.gitconnected.com",
    "blog.devgenius.io", "itnext.io", "codeburst.io",
    "uxplanet.org", "osintteam.blog", "infosecwriteups.com",
    "generativeai.pub", "productcoalition.com", "towardsdev.com",
    "bettermarketing.pub", "eand.co", "betterhumans.pub",
    "uxdesign.cc", "thebolditalic.com", "arcdigital.media",
    "psiloveyou.xyz", "writingcooperative.com",
    "entrepreneurshandbook.co", "prototypr.io", "theascent.pub",
    "storiusmag.com", "artificialcorner.com", "devopsquare.com",
    "javascript.plainenglish.io", "python.plainenglish.io",
    "ai.plainenglish.io", "blog.stackademic.com",
    "ai.gopubby.com", "blog.devops.dev", "code.likeagirl.io",
    "medium.datadriveninvestor.com", "blog.llamaindex.ai",
)

# Medium paragraph types (from GraphQL schema)
class ParagraphType:
    P = "P"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    PRE = "PRE"
    BQ = "BQ"       # Blockquote
    PQ = "PQ"       # Pull quote
    ULI = "ULI"     # Unordered list item
    OLI = "OLI"     # Ordered list item
    IMG = "IMG"
    IFRAME = "IFRAME"
    MIXTAPE_EMBED = "MIXTAPE_EMBED"
    HR = "HR"       # Separator / horizontal rule

# Medium markup types
class MarkupType:
    BOLD = "STRONG"
    ITALIC = "EM"
    CODE = "CODE"
    LINK = "A"
    USER_MENTION = "USER_MENTION"


# ── GraphQL Engine ───────────────────────────────────────────────────────────

# The massive FullPostQuery — this is what cracks the paywall
FULL_POST_QUERY = """query FullPostQuery($postId: ID!, $postMeteringOptions: PostMeteringOptions) { post(id: $postId) { __typename id ...FullPostData } meterPost(postId: $postId, postMeteringOptions: $postMeteringOptions) { __typename ...MeteringInfoData } }  fragment UserFollowData on User { id socialStats { followingCount followerCount } viewerEdge { isFollowing } }  fragment NewsletterData on NewsletterV3 { id viewerEdge { id isSubscribed } }  fragment UserNewsletterData on User { id newsletterV3 { __typename ...NewsletterData } }  fragment ImageMetadataData on ImageMetadata { id originalWidth originalHeight focusPercentX focusPercentY alt }  fragment CollectionFollowData on Collection { id subscriberCount viewerEdge { isFollowing } }  fragment CollectionNewsletterData on Collection { id newsletterV3 { __typename ...NewsletterData } }  fragment BylineData on Post { id readingTime creator { __typename id imageId username name bio tippingLink viewerEdge { isUser } ...UserFollowData ...UserNewsletterData } collection { __typename id name avatar { __typename id ...ImageMetadataData } ...CollectionFollowData ...CollectionNewsletterData } isLocked firstPublishedAt latestPublishedVersion }  fragment ResponseCountData on Post { postResponses { count } }  fragment InResponseToPost on Post { id title creator { name } clapCount responsesCount isLocked }  fragment PostVisibilityData on Post { id collection { viewerEdge { isEditor canEditPosts canEditOwnPosts } } creator { id } isLocked visibility }  fragment PostMenuData on Post { id title creator { __typename ...UserFollowData } collection { __typename ...CollectionFollowData } }  fragment PostMetaData on Post { __typename id title visibility ...ResponseCountData clapCount viewerEdge { clapCount } detectedLanguage mediumUrl readingTime updatedAt isLocked allowResponses isProxyPost latestPublishedVersion isSeries firstPublishedAt previewImage { id } inResponseToPostResult { __typename ...InResponseToPost } inResponseToMediaResource { mediumQuote { startOffset endOffset paragraphs { text type markups { type start end anchorType } } } } inResponseToEntityType canonicalUrl collection { id slug name shortDescription avatar { __typename id ...ImageMetadataData } viewerEdge { isFollowing isEditor canEditPosts canEditOwnPosts isMuting } } creator { id isFollowing name bio imageId mediumMemberAt twitterScreenName viewerEdge { isBlocking isMuting isUser } } previewContent { subtitle } pinnedByCreatorAt ...PostVisibilityData ...PostMenuData }  fragment LinkMetadataList on Post { linkMetadataList { url alts { type url } } }  fragment MediaResourceData on MediaResource { id iframeSrc thumbnailUrl iframeHeight iframeWidth title }  fragment IframeData on Iframe { iframeHeight iframeWidth mediaResource { __typename ...MediaResourceData } }  fragment MarkupData on Markup { name type start end href title rel type anchorType userId creatorIds }  fragment CatalogSummaryData on Catalog { id name description type visibility predefined responsesLocked creator { id name username imageId bio viewerEdge { isUser } } createdAt version itemsLastInsertedAt postItemsCount }  fragment CatalogPreviewData on Catalog { __typename ...CatalogSummaryData id itemsConnection(pagingOptions: { limit: 10 } ) { items { entity { __typename ... on Post { id previewImage { id } } } } paging { count } } }  fragment MixtapeMetadataData on MixtapeMetadata { mediaResourceId href thumbnailImageId mediaResource { mediumCatalog { __typename ...CatalogPreviewData } } }  fragment ParagraphData on Paragraph { id name href text iframe { __typename ...IframeData } layout markups { __typename ...MarkupData } metadata { __typename ...ImageMetadataData } mixtapeMetadata { __typename ...MixtapeMetadataData } type hasDropCap dropCapImage { __typename ...ImageMetadataData } codeBlockMetadata { lang mode } }  fragment QuoteData on Quote { id postId userId startOffset endOffset paragraphs { __typename id ...ParagraphData } quoteType }  fragment HighlightsData on Post { id highlights { __typename ...QuoteData } }  fragment PostFooterCountData on Post { __typename id clapCount viewerEdge { clapCount } ...ResponseCountData responsesLocked mediumUrl title collection { id viewerEdge { isMuting isFollowing } } creator { id viewerEdge { isMuting isFollowing } } }  fragment TagNoViewerEdgeData on Tag { id normalizedTagSlug displayTitle followerCount postCount }  fragment VideoMetadataData on VideoMetadata { videoId previewImageId originalWidth originalHeight }  fragment SectionData on Section { name startIndex textLayout imageLayout videoLayout backgroundImage { __typename ...ImageMetadataData } backgroundVideo { __typename ...VideoMetadataData } }  fragment PostBodyData on RichText { sections { __typename ...SectionData } paragraphs { __typename id ...ParagraphData } }  fragment FullPostData on Post { __typename ...BylineData ...PostMetaData ...LinkMetadataList ...HighlightsData ...PostFooterCountData tags { __typename id ...TagNoViewerEdgeData } content(postMeteringOptions: $postMeteringOptions) { bodyModel { __typename ...PostBodyData } validatedShareKey } }  fragment MeteringInfoData on MeteringInfo { maxUnlockCount unlocksRemaining postIds }"""


def generate_random_sha256():
    return hashlib.sha256(secrets.token_bytes()).hexdigest()


def get_unix_ms() -> int:
    return int(datetime.now().timestamp() * 1000)


# ── URL → Post ID Extraction ────────────────────────────────────────────────

def extract_post_id(url: str) -> Optional[str]:
    """
    Extract Medium post ID from URL slug.
    Medium post IDs are 8-12 character hex strings at the end of the slug.
    Example: "my-article-title-5932aab1b6d0" → "5932aab1b6d0"
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Handle /p/<id> mobile links
    if "/p/" in path:
        post_id = path.split("/p/")[-1]
        if _is_valid_post_id(post_id):
            return post_id

    # Standard: last path segment, split by '-', hex at the end
    slug = path.split("/")[-1]
    if not slug:
        return None

    # Try: hex after last dash
    post_id = slug.split("-")[-1]
    if _is_valid_post_id(post_id):
        return post_id

    # Fallback: find any 8-12 char hex in the slug
    matches = re.findall(r"[a-fA-F0-9]{8,12}", slug)
    if matches:
        return matches[-1]

    return None


def _is_valid_post_id(hex_string: str) -> bool:
    """Check if string looks like a Medium post ID (8-12 hex chars)."""
    if not hex_string or len(hex_string) not in range(8, 13):
        return False
    return all(c in VALID_ID_CHARS for c in hex_string)


def is_medium_url(url: str) -> bool:
    """Check if URL belongs to a Medium domain."""
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").removeprefix("www.")
        # Direct domain match
        if any(host == d or host.endswith(f".{d}") for d in KNOWN_MEDIUM_DOMAINS):
            return True
        # Custom domain — check if slug has a valid post ID pattern
        slug = parsed.path.split("/")[-1] if parsed.path else ""
        if slug and extract_post_id(url):
            return True  # Possibly a custom Medium domain
        return False
    except Exception:
        return False


# ── GraphQL Fetcher ──────────────────────────────────────────────────────────

async def fetch_via_graphql(post_id: str) -> dict:
    """
    Fetch full article via Medium's private GraphQL API.
    Uses curl_cffi for TLS fingerprint impersonation.
    """
    from curl_cffi.requests import AsyncSession

    headers = {
        "X-APOLLO-OPERATION-ID": generate_random_sha256(),
        "X-APOLLO-OPERATION-NAME": "FullPostQuery",
        "Accept": "multipart/mixed; deferSpec=20220824, application/json, application/json",
        "Accept-Language": "en-US",
        "X-Obvious-CID": "android",
        "X-Xsrf-Token": "1",
        "X-Client-Date": str(get_unix_ms()),
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        "Cache-Control": "public, max-age=-1",
        "Content-Type": "application/json",
        "Connection": "Keep-Alive",
    }

    graphql_data = {
        "operationName": "FullPostQuery",
        "variables": {
            "postId": post_id,
            "postMeteringOptions": {},
        },
        "query": FULL_POST_QUERY,
    }

    try:
        async with AsyncSession() as session:
            response = await session.post(
                "https://medium.com/_/graphql",
                headers=headers,
                json=graphql_data,
                timeout=TIMEOUT,
                impersonate="chrome110",
            )

            if response.status_code != 200:
                logger.error(f"GraphQL failed for {post_id}: HTTP {response.status_code}")
                raise HTTPException(502, f"Medium API returned {response.status_code}")

            return response.json()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"GraphQL request failed: {e}")
        raise HTTPException(502, f"Failed to reach Medium API: {e}")


# ── GraphQL Response → Article Data ──────────────────────────────────────────

def parse_graphql_response(data: dict, original_url: str) -> dict:
    """Parse the GraphQL JSON response into our article structure."""
    post = data.get("data", {}).get("post")
    if not post:
        raise HTTPException(404, "Article not found or has been deleted")

    # Title
    title = post.get("title", "Untitled")

    # Author
    creator = post.get("creator", {})
    author = creator.get("name", "Unknown")
    author_username = creator.get("username", "")
    author_img_id = creator.get("imageId", "")
    author_img = f"https://miro.medium.com/v2/resize:fill:88:88/{author_img_id}" if author_img_id else ""

    # Publication
    collection = post.get("collection", {}) or {}
    publication = collection.get("name", "")

    # Date
    first_published = post.get("firstPublishedAt")
    pub_date = _format_timestamp(first_published) if first_published else None

    # Reading time & claps
    reading_time = round(post.get("readingTime", 0))
    claps = post.get("clapCount", 0)
    claps_str = _format_claps(claps)

    # Responses
    responses = (post.get("postResponses") or {}).get("count", 0)

    # Tags
    tags = []
    for tag in (post.get("tags") or [])[:5]:
        tag_text = tag.get("displayTitle") or tag.get("normalizedTagSlug", "")
        if tag_text:
            tags.append(tag_text)

    # Featured / preview image
    preview_img = post.get("previewImage", {}) or {}
    preview_img_id = preview_img.get("id", "")
    featured_img = f"https://miro.medium.com/v2/resize:fit:1400/{preview_img_id}" if preview_img_id else None

    # Content — parse paragraphs from bodyModel
    content_data = post.get("content", {}) or {}
    body_model = content_data.get("bodyModel", {}) or {}
    paragraphs = body_model.get("paragraphs", [])
    content_html = render_paragraphs(paragraphs)

    # Word count
    text_only = re.sub(r"<[^>]+>", "", content_html)
    word_count = len(text_only.split())

    # Medium URL
    medium_url = post.get("mediumUrl", original_url)

    return {
        "title": title,
        "author": author,
        "author_username": author_username,
        "author_img": author_img,
        "publication": publication,
        "url": medium_url,
        "original_url": original_url,
        "pub_date": pub_date,
        "featured_img": featured_img,
        "content": content_html,
        "reading_time": reading_time if reading_time else max(1, word_count // 200),
        "word_count": word_count,
        "tags": tags,
        "claps": claps_str,
        "responses": responses,
        "fetch_method": "graphql",
    }


def _format_timestamp(ts) -> str:
    """Convert Unix ms timestamp to human readable date."""
    try:
        dt = datetime.fromtimestamp(int(ts) / 1000)
        return dt.strftime("%B %d, %Y")
    except Exception:
        return str(ts)


def _format_claps(count: int) -> str:
    """Format clap count like Medium (1.2K, etc)."""
    if count >= 1000:
        return f"{count / 1000:.1f}K"
    return str(count)


# ── Paragraph & Markup Renderer ──────────────────────────────────────────────

def render_paragraphs(paragraphs: list) -> str:
    """Convert Medium's paragraph array to HTML."""
    html_parts = []
    in_ul = False
    in_ol = False

    for para in paragraphs:
        p_type = para.get("type", "P")
        text = para.get("text", "")
        markups = para.get("markups", [])
        metadata = para.get("metadata") or {}
        iframe = para.get("iframe") or {}
        mixtape = para.get("mixtapeMetadata") or {}
        code_meta = para.get("codeBlockMetadata") or {}

        # Close list tags if switching type
        if p_type != "ULI" and in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if p_type != "OLI" and in_ol:
            html_parts.append("</ol>")
            in_ol = False

        # Apply inline markups (bold, italic, code, links)
        rendered_text = apply_markups(text, markups)

        if p_type == "H2":
            html_parts.append(f'<h2>{rendered_text}</h2>')

        elif p_type == "H3":
            html_parts.append(f'<h3>{rendered_text}</h3>')

        elif p_type == "H4":
            html_parts.append(f'<h4>{rendered_text}</h4>')

        elif p_type == "PRE":
            lang = code_meta.get("lang", "")
            lang_attr = f' class="language-{lang}"' if lang else ""
            escaped = html.escape(text)
            html_parts.append(f'<pre><code{lang_attr}>{escaped}</code></pre>')

        elif p_type == "BQ" or p_type == "PQ":
            html_parts.append(f'<blockquote>{rendered_text}</blockquote>')

        elif p_type == "ULI":
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            html_parts.append(f"<li>{rendered_text}</li>")

        elif p_type == "OLI":
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            html_parts.append(f"<li>{rendered_text}</li>")

        elif p_type == "IMG":
            img_id = metadata.get("id", "")
            alt = metadata.get("alt") or text or ""
            if img_id:
                src = f"https://miro.medium.com/v2/resize:fit:1400/{img_id}"
                caption = f"<figcaption>{html.escape(text)}</figcaption>" if text else ""
                html_parts.append(
                    f'<figure><img src="{src}" alt="{html.escape(alt)}" loading="lazy">{caption}</figure>'
                )

        elif p_type == "IFRAME":
            media_res = iframe.get("mediaResource") or {}
            iframe_src = media_res.get("iframeSrc", "")
            iframe_title = media_res.get("title", "")
            iframe_w = iframe.get("iframeWidth") or 800
            iframe_h = iframe.get("iframeHeight") or 450
            if iframe_src:
                html_parts.append(
                    f'<div class="embed-container">'
                    f'<iframe src="{iframe_src}" width="{iframe_w}" height="{iframe_h}" '
                    f'title="{html.escape(iframe_title)}" frameborder="0" '
                    f'allowfullscreen loading="lazy"></iframe></div>'
                )
            elif text:
                html_parts.append(f"<p>{rendered_text}</p>")

        elif p_type == "MIXTAPE_EMBED":
            href = mixtape.get("href", "")
            if href:
                lines = text.split("\n") if text else [""]
                embed_title = html.escape(lines[0]) if lines else ""
                embed_desc = html.escape(lines[1]) if len(lines) > 1 else ""
                html_parts.append(
                    f'<div class="mixtape-embed">'
                    f'<a href="{href}" target="_blank" rel="noopener">'
                    f'<strong>{embed_title}</strong>'
                    f'{"<br><span>" + embed_desc + "</span>" if embed_desc else ""}'
                    f'</a></div>'
                )
            else:
                html_parts.append(f"<p>{rendered_text}</p>")

        elif p_type == "HR":
            html_parts.append("<hr>")

        else:
            # Default: paragraph
            if rendered_text.strip():
                html_parts.append(f"<p>{rendered_text}</p>")

    # Close any open lists
    if in_ul:
        html_parts.append("</ul>")
    if in_ol:
        html_parts.append("</ol>")

    return "\n".join(html_parts)


def apply_markups(text: str, markups: list) -> str:
    """Apply inline markups (bold, italic, code, links) to paragraph text."""
    if not markups or not text:
        return html.escape(text)

    # Sort markups by start position, then by longest first (for nesting)
    sorted_markups = sorted(markups, key=lambda m: (m.get("start", 0), -m.get("end", 0)))

    # Build character-level tag insertion
    # We'll use a simple approach: convert to list, insert tags
    chars = list(text)
    n = len(chars)

    # We need to track open/close positions
    opens = {}   # position -> list of opening tags
    closes = {}  # position -> list of closing tags

    for markup in sorted_markups:
        m_type = markup.get("type", "")
        start = max(0, markup.get("start", 0))
        end = min(n, markup.get("end", n))
        href = markup.get("href", "")
        user_id = markup.get("userId", "")

        if m_type == "STRONG":
            opens.setdefault(start, []).append("<strong>")
            closes.setdefault(end, []).insert(0, "</strong>")
        elif m_type == "EM":
            opens.setdefault(start, []).append("<em>")
            closes.setdefault(end, []).insert(0, "</em>")
        elif m_type == "CODE":
            opens.setdefault(start, []).append("<code>")
            closes.setdefault(end, []).insert(0, "</code>")
        elif m_type == "A" and href:
            opens.setdefault(start, []).append(f'<a href="{html.escape(href)}" target="_blank" rel="noopener">')
            closes.setdefault(end, []).insert(0, "</a>")
        elif m_type == "A" and user_id:
            opens.setdefault(start, []).append(f'<a href="https://medium.com/u/{user_id}" target="_blank" rel="noopener">')
            closes.setdefault(end, []).insert(0, "</a>")

    # Build result
    result = []
    for i, char in enumerate(chars):
        # Insert closing tags first (LIFO order)
        if i in closes:
            result.extend(closes[i])
        # Then opening tags
        if i in opens:
            result.extend(opens[i])
        result.append(html.escape(char))

    # Close any remaining tags at the end
    if n in closes:
        result.extend(closes[n])

    return "".join(result)


# ── Mirror Proxy Scraper (primary content source) ────────────────────────────

UPSTREAM_MIRRORS = [
    "https://freedium-mirror.cfd",
    "https://freedium.cfd",
]


async def fetch_via_proxy(url: str) -> dict | None:
    """
    Fetch full premium article via upstream mirror proxy.
    The proxy renders the full content — we scrape and parse it.
    """
    from curl_cffi.requests import AsyncSession
    from bs4 import BeautifulSoup

    for mirror in UPSTREAM_MIRRORS:
        proxy_url = f"{mirror}/{url}"
        logger.info(f"Trying mirror: {proxy_url}")

        try:
            async with AsyncSession() as session:
                resp = await session.get(
                    proxy_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                    timeout=30,
                    impersonate="chrome110",
                    allow_redirects=True,
                )

                if resp.status_code != 200:
                    logger.warning(f"Mirror {mirror} returned {resp.status_code}")
                    continue

                article = parse_proxy_html(resp.text, url)
                if article and article.get("content") and len(article["content"]) > 500:
                    article["fetch_method"] = "proxy"
                    logger.info(f"Mirror success: {len(article['content'])} chars of content")
                    return article
                else:
                    logger.warning(f"Mirror returned insufficient content from {mirror}")

        except Exception as e:
            logger.warning(f"Mirror {mirror} failed: {e}")
            continue

    return None


def parse_proxy_html(html_text: str, original_url: str) -> dict | None:
    """Parse upstream proxy's rendered HTML into our article structure."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_text, "html.parser")

    # Remove scripts, styles, nav, footer, proxy UI chrome
    for tag in soup.find_all(["script", "style", "nav", "footer", "header",
                              "aside", "noscript"]):
        tag.decompose()

    # Remove proxy's own UI elements (notifications, modals, banners)
    for sel in [".storage-notification-container", ".modal",
                "[class*='notification']", "[class*='donate']",
                "[class*='fixed'][class*='bottom']",
                "[class*='fixed'][class*='top'][class*='right']"]:
        for el in soup.select(sel):
            el.decompose()

    # Title — h1 inside the content div
    title = None
    h1 = soup.select_one("h1")
    if h1:
        title = h1.get_text(strip=True)
    if not title:
        title = soup.title.get_text(strip=True) if soup.title else "Untitled"
        # Clean proxy suffix from title
        title = re.sub(r"\s*\|.*$", "", title)
        title = re.sub(r"\s*[-–—]\s*(Freedium|ReadMedium)\s*$", "", title)

    # Author — proxy puts author links as a[href*="medium.com/@"]
    # The second link typically has the author name text (first wraps avatar)
    author = "Unknown"
    author_username = ""
    author_img = ""
    author_links = soup.select('a[href*="medium.com/@"]')
    for al in author_links:
        name = al.get_text(strip=True)
        if name and name != "Follow" and len(name) > 1:
            author = name
            href = al.get("href", "")
            if "/@" in href:
                author_username = href.split("/@")[-1].split("/")[0].split("?")[0]
            break

    # Author avatar — img.rounded-full
    avatar_img = soup.select_one("img.rounded-full")
    if avatar_img and avatar_img.get("src"):
        author_img = avatar_img["src"]

    # Publication date — look for any date text near the author section
    pub_date = None
    # Dates in spans with text-sm class
    for el in soup.select("span.text-sm, span.text-xs"):
        txt = el.get_text(strip=True)
        # Look for date-like patterns: "Apr 20, 2026" or "2 days ago" etc.
        if re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4}|ago|days|hours)", txt):
            pub_date = txt
            break

    # Featured image — first full-size img (not the avatar)
    featured_img = None
    for img in soup.select("img"):
        src = img.get("src", "")
        classes = img.get("class", [])
        # Skip avatar images and tiny icons
        if "rounded-full" in classes or "no-lightense" in classes:
            continue
        if "miro.medium.com" in src and "resize:fit" in src:
            featured_img = src
            break

    # Main content — look for the content container
    content_html = ""
    for sel in [".main-content", ".post-content", "article", ".content",
                "main", ".post-body"]:
        el = soup.select_one(sel)
        if el:
            # Remove the title from content if it's duplicated
            first_h1 = el.find("h1")
            if first_h1 and first_h1.get_text(strip=True) == title:
                first_h1.decompose()

            # Remove author info block from content
            for author_block in el.select("[class*='author'], [class*='byline']"):
                author_block.decompose()

            # Clean up proxy-specific elements inside content
            for junk in el.select("[class*='freedium'], [class*='banner'], "
                                  "[class*='subscribe'], [class*='membership']"):
                junk.decompose()

            content_html = el.decode_contents()
            break

    if not content_html:
        # Fallback: grab all content-ish tags
        parts = []
        for tag in soup.find_all(["p", "h2", "h3", "h4", "pre", "blockquote",
                                  "figure", "ul", "ol"]):
            if tag.get_text(strip=True):
                parts.append(str(tag))
        content_html = "\n".join(parts)

    # Clean remaining empty elements
    content_soup = BeautifulSoup(content_html, "html.parser")
    for p in content_soup.find_all("p"):
        if not p.get_text(strip=True) and not p.find("img"):
            p.decompose()
    content_html = content_soup.decode_contents()

    # Word count & reading time
    text_only = re.sub(r"<[^>]+>", "", content_html)
    word_count = len(text_only.split())
    reading_time = max(1, word_count // 200)

    # Tags
    tags = []
    for tag_el in soup.select("[class*='tag'] a, .tags a, .post-tags a"):
        tag_text = tag_el.get_text(strip=True)
        if tag_text and tag_text not in tags:
            tags.append(tag_text)

    return {
        "title": title,
        "author": author,
        "author_username": author_username,
        "author_img": author_img,
        "publication": "",
        "url": original_url,
        "original_url": original_url,
        "pub_date": pub_date,
        "featured_img": featured_img,
        "content": content_html,
        "reading_time": reading_time,
        "word_count": word_count,
        "tags": tags[:5],
        "claps": "",
        "responses": 0,
        "fetch_method": "proxy",
    }


# ── Full Fetch Pipeline ──────────────────────────────────────────────────────

async def fetch_article(url: str) -> dict:
    """Main entry point: URL → parsed article dict."""
    post_id = extract_post_id(url)
    if not post_id:
        raise HTTPException(422, f"Could not extract post ID from URL: {url}")

    logger.info(f"Extracted post_id={post_id} from {url}")

    # Strategy 1: Mirror proxy (full premium content, no subscription needed)
    article = await fetch_via_proxy(url)
    if article:
        return article

    logger.info("Mirror proxy failed, falling back to direct GraphQL...")

    # Strategy 2: Direct GraphQL (needs MEDIUM_AUTH_COOKIES for full content)
    graphql_data = await fetch_via_graphql(post_id)
    article = parse_graphql_response(graphql_data, url)

    if not article.get("content"):
        raise HTTPException(422, "Could not fetch article content from any source")

    return article


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/read", response_class=HTMLResponse)
async def read_page(request: Request, url: str = ""):
    if not url:
        return templates.TemplateResponse(request, "index.html", {"error": "No URL provided"})
    try:
        article = await fetch_article(url)
    except HTTPException as e:
        return templates.TemplateResponse(request, "index.html", {"error": e.detail})
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return templates.TemplateResponse(request, "index.html", {"error": f"Failed to fetch article: {e}"})
    return templates.TemplateResponse(request, "article.html", {"article": article})


@app.get("/api/fetch")
async def api_fetch(url: str):
    if not url:
        raise HTTPException(400, "url parameter required")
    article = await fetch_article(url)
    return JSONResponse(article)


@app.get("/health")
async def health():
    return {"status": "alive", "version": "2.0.0", "method": "proxy+graphql", "author": "Elliot Jr aka bratyabasu07"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
