"""Browser launching, URL navigation, and web search tools."""

import os
import urllib.parse
import webbrowser
from jarvis.actions.registry import ToolResult, tool


@tool(
    name="open_browser",
    description="Open the user's web browser (Chrome, Edge, Firefox, Brave, or default).",
    params={"browser": {"type": "string", "description": "Optional browser name: 'chrome', 'edge', 'firefox', 'brave', or 'default'", "required": False}},
    risk="low",
)
def open_browser(browser: str = "default") -> ToolResult:
    """Launch the browser."""
    try:
        browser_lower = browser.lower().strip()
        if browser_lower in ["default", "", "none"]:
            webbrowser.open("about:blank")
            return ToolResult(ok=True, message="Opening your browser.")

        # Try specific browser controller
        try:
            controller = webbrowser.get(browser_lower)
            controller.open("about:blank")
            return ToolResult(ok=True, message=f"Opening {browser.title()}.")
        except Exception:
            # Fallback to general open
            webbrowser.open("about:blank")
            return ToolResult(ok=True, message=f"Opening browser.")
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to open browser: {e}")


@tool(
    name="open_url",
    description="Open a specific website URL in the default browser.",
    params={"url": {"type": "string", "description": "The web address URL to navigate to (e.g. 'https://github.com')"}},
    risk="low",
)
def open_url(url: str) -> ToolResult:
    """Open a web URL."""
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    try:
        webbrowser.open(url)
        return ToolResult(ok=True, message=f"Opening {url}.", data={"url": url})
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to open URL: {e}")


@tool(
    name="web_search",
    description="Search the web for a query using Google or default search engine.",
    params={"query": {"type": "string", "description": "The search query keywords"}},
    risk="low",
)
def web_search(query: str) -> ToolResult:
    """Execute a web search in the browser."""
    encoded_query = urllib.parse.quote_plus(query.strip())
    search_url = f"https://www.google.com/search?q={encoded_query}"

    try:
        webbrowser.open(search_url)
        return ToolResult(
            ok=True,
            message=f"Searching for {query}.",
            data={"query": query, "url": search_url},
        )
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to run web search: {e}")


@tool(
    name="open_site",
    description="Open a well-known site (e.g. 'youtube', 'github', 'reddit', 'gmail', 'wikipedia', 'chatgpt').",
    params={"site_name": {"type": "string", "description": "Name of the website"}},
    risk="low",
)
def open_site(site_name: str) -> ToolResult:
    """Open common named web destinations."""
    common_sites = {
        "youtube": "https://www.youtube.com",
        "github": "https://www.github.com",
        "reddit": "https://www.reddit.com",
        "gmail": "https://mail.google.com",
        "google": "https://www.google.com",
        "chatgpt": "https://chatgpt.com",
        "wikipedia": "https://www.wikipedia.org",
        "twitter": "https://x.com",
        "x": "https://x.com",
        "netflix": "https://www.netflix.com",
        "spotify": "https://open.spotify.com",
        "amazon": "https://www.amazon.com",
        "linkedin": "https://www.linkedin.com",
    }

    clean_site = site_name.lower().strip()
    if clean_site in common_sites:
        target_url = common_sites[clean_site]
    else:
        target_url = f"https://www.{clean_site}.com"

    try:
        webbrowser.open(target_url)
        return ToolResult(ok=True, message=f"Opening {clean_site.title()}.", data={"url": target_url})
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to open {site_name}: {e}")
