#!/usr/bin/env python3
"""Generate the bundled landing page (av_mcp/static/index.html) from README.md.

The MCP server serves its own landing page so it no longer depends on the
CloudFront/S3 static site (todo 2600). README.md stays the single source of
truth for the landing content: this script inlines it into a self-contained
HTML shell (inline CSS + a small client-side markdown render via marked) that
the Lambda returns verbatim for ``GET /``.

The generated index.html is NOT committed (see .gitignore); CI regenerates it
before ``sam build`` in .github/workflows/deploy.yml. For local dev / local
sam build, run this once after editing README.md so the file exists:

    python mcp/build_static_pages.py
"""

from pathlib import Path

MCP_DIR = Path(__file__).resolve().parent
README_PATH = MCP_DIR.parent / "README.md"
OUTPUT_PATH = MCP_DIR / "src" / "av_mcp" / "static" / "index.html"

# Self-contained landing shell. Mirrors web/components/PostPage.tsx + Markdown.tsx:
# dark (rgb(45,45,45)) background, Alpha Vantage header, a green-bordered article
# card with the logo, README rendered as markdown, and the footer. The README is
# embedded verbatim in a non-executed <script type="text/markdown"> block (at the
# __README__ placeholder) and rendered client-side with marked; raw HTML in the
# README (<details>, <img>, onclick) is passed through, matching rehype-raw.
TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alpha Vantage MCP Server</title>
<link rel="icon" href="https://cdn.alphavantage.co/logo.png">
<script src="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"></script>
<style>
  :root { --av-green: #42DCA3; --av-card: #1f1f1f; --av-border: rgba(74, 222, 128, 0.3); }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    background-color: rgb(45, 45, 45);
    color: #d1d5db;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    min-height: 100vh;
  }
  header { padding: 2rem 1rem 1rem; }
  .bar {
    max-width: 900px; margin: 0 auto;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;
  }
  .brand { color: #fff; font-size: 1.25rem; letter-spacing: 0.1em; text-decoration: none; }
  .brand span { font-weight: 300; }
  .nav { display: flex; gap: 1.5rem; }
  .nav a, a { color: var(--av-green); text-decoration: none; }
  .nav a:hover, a:hover { text-decoration: underline; }
  main { display: flex; justify-content: center; padding: 1rem; }
  article {
    width: 100%; max-width: 820px;
    background-color: var(--av-card);
    border: 1px solid var(--av-border);
    border-radius: 0.5rem;
    padding: 1.5rem;
  }
  @media (min-width: 640px) { article { padding: 2rem; } }
  .logo { text-align: center; margin-bottom: 3rem; }
  .logo img { height: 4rem; }
  .content h1 { display: none; }
  .content h2 { color: var(--av-green); font-weight: 300; font-size: 1.875rem; margin: 2rem 0 1.5rem; }
  .content h3 { color: var(--av-green); font-weight: 300; font-size: 1.5rem; margin: 1.5rem 0 1rem; }
  .content h4 { color: var(--av-green); font-weight: 600; font-size: 1.25rem; margin: 1rem 0; }
  .content h5, .content h6 { color: #fff; font-weight: 700; margin: 0.75rem 0 0.25rem; }
  .content p { color: #d1d5db; margin: 1rem 0; }
  .content strong { color: var(--av-green); }
  .content em { color: #9ca3af; }
  .content ul { list-style: disc; padding-left: 1.5rem; }
  .content ol { list-style: decimal; padding-left: 1.5rem; }
  .content li { color: #d1d5db; margin: 0.5rem 0; }
  .content blockquote {
    border-left: 4px solid var(--av-border); background-color: var(--av-card);
    padding: 0.5rem 1rem; margin: 1rem 0; border-radius: 0 0.375rem 0.375rem 0;
    color: #9ca3af; font-style: italic;
  }
  .content code {
    background-color: var(--av-card); color: var(--av-green);
    border: 1px solid var(--av-border); border-radius: 0.25rem;
    padding: 0.1rem 0.4rem; font-size: 0.875rem;
  }
  .content pre {
    background-color: var(--av-card); color: var(--av-green);
    border: 1px solid var(--av-border); border-radius: 0.375rem;
    padding: 1rem; overflow-x: auto; margin: 1rem 0;
  }
  .content pre code { border: none; padding: 0; background: none; }
  /* Per-code-block copy button (ported from web/components/Markdown.tsx pre wrapper).
     Wraps each <pre> in a relative container; the button reveals on hover (top-right)
     and swaps copy icon -> checkmark for 2s on success. */
  .content .code-block { position: relative; }
  .content .copy-btn {
    position: absolute; top: 0.5rem; right: 0.5rem; padding: 0.25rem;
    display: flex; align-items: center; justify-content: center;
    background-color: rgba(66, 220, 163, 0.1); color: var(--av-green);
    border: none; border-radius: 0.25rem; cursor: pointer;
    opacity: 0; transition: all 0.2s ease;
  }
  .content .code-block:hover .copy-btn { opacity: 1; }
  .content .copy-btn:hover { background-color: rgba(66, 220, 163, 0.2); transform: scale(1.05); }
  /* Single-line blocks: vertically center the button next to the lone line. */
  .content .code-block--single .copy-btn { top: 50%; transform: translateY(-50%); }
  .content .code-block--single .copy-btn:hover { transform: translateY(-50%) scale(1.05); }
  .content hr { border: none; border-top: 1px solid var(--av-border); margin: 2rem 0; }
  .content table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; display: block; overflow-x: auto; }
  .content th { border: 1px solid var(--av-border); color: var(--av-green); background-color: var(--av-card); padding: 0.5rem 1rem; }
  .content td { border: 1px solid var(--av-border); color: #d1d5db; padding: 0.5rem 1rem; }
  .content img { max-width: 100%; height: auto; }
  .content details { border: 1px solid var(--av-border); background-color: var(--av-card); border-radius: 0.5rem; margin: 1rem 0; overflow: hidden; }
  .content summary { cursor: pointer; font-weight: 600; color: var(--av-green); background-color: rgba(66, 220, 163, 0.1); padding: 1rem; }
  .content details[open] { padding: 0 1rem 1rem; }
  .content details[open] summary { border-bottom: 1px solid var(--av-border); margin: 0 -1rem 1rem; }
  .content .youtube-embed { margin: 1.5rem 0; text-align: center; }
  .content .youtube-embed iframe { width: 100%; max-width: 42rem; aspect-ratio: 16 / 9; border: 0; border-radius: 0.5rem; }
  footer { padding: 2rem 1rem; text-align: center; color: #9ca3af; font-size: 0.875rem; }
  footer p { margin: 0.25rem 0; }
  .content h2, .content h3 { scroll-margin-top: 1.5rem; }
  /* Table of contents (ported from web/components/TOCDesktop.tsx + TOCMobile.tsx). */
  .toc-title {
    color: var(--av-green); font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.05em; font-size: 0.75rem; margin-bottom: 0.75rem;
  }
  .toc-nav ul { list-style: none; margin: 0; padding: 0; }
  .toc-nav li { margin: 0; }
  .toc-nav a {
    display: block; color: #9ca3af; text-decoration: none;
    padding: 0.25rem 0.6rem; border-left: 2px solid transparent;
    border-radius: 0 0.25rem 0.25rem 0; line-height: 1.35;
  }
  .toc-nav a:hover { color: var(--av-green); text-decoration: none; background-color: rgba(66, 220, 163, 0.08); }
  .toc-nav a.toc-h3 { padding-left: 1.4rem; font-size: 0.8125rem; }
  .toc-nav a.active { color: var(--av-green); border-left-color: var(--av-green); background-color: rgba(66, 220, 163, 0.12); }
  .toc-desktop {
    /* Anchor to the gutter left of the centered 820px article: its right edge sits
       a constant 24px from the article (17.5rem = 16rem width + 1.5rem gap). Only
       shown at >=1444px (see media query), the point where the left edge clears 2rem
       without clamping, so it never overlaps the article. */
    position: fixed; left: calc(50vw - 410px - 17.5rem); top: 6rem; width: 16rem;
    max-height: 64vh; overflow-y: auto;
    background-color: var(--av-card); border: 1px solid var(--av-border);
    border-radius: 0.5rem; padding: 1rem; font-size: 0.875rem; z-index: 10;
    display: none;
  }
  /* Hide the scrollbar but keep the TOC panels scrollable. */
  .toc-desktop, .toc-mobile { scrollbar-width: none; -ms-overflow-style: none; }
  .toc-desktop::-webkit-scrollbar, .toc-mobile::-webkit-scrollbar { display: none; }
  .toc-toggle {
    position: fixed; bottom: 1.5rem; right: 1.5rem; width: 3rem; height: 3rem;
    border-radius: 9999px; background-color: var(--av-green); color: rgb(45, 45, 45);
    border: none; cursor: pointer; z-index: 20;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  }
  .toc-mobile {
    position: fixed; bottom: 5rem; right: 1.5rem; width: 16rem;
    max-height: 60vh; overflow-y: auto;
    background-color: var(--av-card); border: 1px solid var(--av-border);
    border-radius: 0.5rem; padding: 1rem; font-size: 0.875rem; z-index: 20;
    display: none;
  }
  .toc-mobile.open { display: block; }
  /* 1444px = 410px (half article) + 17.5rem (sidebar + gap) + 2rem (edge margin),
     scaled by 2 for 50vw: below this the gutter can't fit the sidebar, so the
     floating toggle handles the TOC instead. */
  @media (min-width: 1444px) {
    .toc-desktop { display: block; }
    .toc-toggle, .toc-mobile { display: none !important; }
  }
</style>
</head>
<body>
  <header>
    <div class="bar">
      <a class="brand" href="https://www.alphavantage.co/">ALPHA <span>VANTAGE</span></a>
      <nav class="nav">
        <a href="https://www.alphavantage.co/">Alpha Vantage Home</a>
        <a href="https://www.alphavantage.co/documentation/">API Documentation</a>
      </nav>
    </div>
  </header>
  <main>
    <article>
      <div class="logo">
        <img src="https://cdn.alphavantage.co/logo.png" alt="Alpha Vantage Logo">
      </div>
      <div class="content" id="content"></div>
    </article>
  </main>
  <aside class="toc-desktop" aria-label="Table of contents">
    <div class="toc-title">On this page</div>
    <nav class="toc-nav" id="toc-desktop-nav"></nav>
  </aside>
  <button class="toc-toggle" id="toc-toggle" aria-label="Toggle table of contents" aria-expanded="false">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
  </button>
  <aside class="toc-mobile" id="toc-mobile" aria-label="Table of contents">
    <div class="toc-title">On this page</div>
    <nav class="toc-nav" id="toc-mobile-nav"></nav>
  </aside>
  <footer>
    <p>Made with love at <a href="https://www.alphavantage.co/" target="_blank" rel="noopener noreferrer">Alpha Vantage</a>. Happy hacking!</p>
    <p><a href="https://www.alphavantage.co/privacy/" target="_blank" rel="noopener noreferrer">Privacy Policy</a></p>
  </footer>

  <script type="text/markdown" id="readme-source">
__README__
  </script>

  <script>
    // Slugify headings the same way web/lib/toc.ts does, so the README's in-page
    // anchor links (e.g. [core_stock_apis](#core_stock_apis)) resolve.
    function slugify(text) {
      var slug = text.toLowerCase()
        .replace(/[^\\p{L}\\p{N}\\s-]/gu, '')
        .replace(/\\s+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
      return slug || 'heading';
    }

    // Convert YouTube thumbnail links to iframe embeds (mirrors Markdown.tsx).
    function preprocess(md) {
      var pattern = /\\[!\\[([^\\]]*)\\]\\(https?:\\/\\/(?:img\\.youtube\\.com|i\\d*\\.ytimg\\.com)\\/vi\\/([^\\/]+)\\/[^)]+\\)\\]\\(https:\\/\\/www\\.youtube\\.com\\/watch\\?v=([^)]+)\\)/g;
      return md.replace(pattern, function (_m, _alt, _thumb, id) {
        return '<div class="youtube-embed"><iframe src="https://www.youtube.com/embed/' + id + '" allowfullscreen></iframe></div>';
      });
    }

    var source = document.getElementById('readme-source').textContent;
    var renderer = new marked.Renderer();
    renderer.heading = function (text, level) {
      var id = slugify(text.replace(/<[^>]+>/g, ''));
      return '<h' + level + ' id="' + id + '">' + text + '</h' + level + '>';
    };
    marked.setOptions({ renderer: renderer, gfm: true, breaks: false });
    document.getElementById('content').innerHTML = marked.parse(preprocess(source));

    // Build the table of contents from the already-rendered headings (their ids
    // were assigned by renderer.heading above), then wire active-section
    // highlighting and the mobile toggle. Ports web/components/TOCDesktop.tsx +
    // TOCMobile.tsx + useTocNavigation.tsx into vanilla JS.
    (function buildToc() {
      var headings = document.querySelectorAll('#content h2[id], #content h3[id]');
      if (!headings.length) return;
      var items = [];
      headings.forEach(function (h) {
        var cls = h.tagName === 'H3' ? 'toc-h3' : 'toc-h2';
        var a = document.createElement('a');
        a.className = cls;
        a.href = '#' + h.id;
        a.textContent = h.textContent;
        items.push('<li>' + a.outerHTML + '</li>');
      });
      var html = '<ul>' + items.join('') + '</ul>';
      document.getElementById('toc-desktop-nav').innerHTML = html;
      document.getElementById('toc-mobile-nav').innerHTML = html;

      var links = document.querySelectorAll('.toc-nav a');
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var target = '#' + entry.target.id;
          links.forEach(function (a) {
            a.classList.toggle('active', a.getAttribute('href') === target);
          });
        });
      }, { rootMargin: '-20% 0px -80% 0px' });
      headings.forEach(function (h) { observer.observe(h); });

      // Mobile: floating button reveals the same nav; tapping an item closes it.
      var toggle = document.getElementById('toc-toggle');
      var mobile = document.getElementById('toc-mobile');
      toggle.addEventListener('click', function () {
        var open = mobile.classList.toggle('open');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
      document.getElementById('toc-mobile-nav').addEventListener('click', function (e) {
        if (e.target.closest('a')) {
          mobile.classList.remove('open');
          toggle.setAttribute('aria-expanded', 'false');
        }
      });
    })();

    // Wrap every rendered <pre> with a hover-reveal copy-to-clipboard button
    // (ports the pre wrapper from web/components/Markdown.tsx). Covers the MCP
    // endpoint URL, which lives in a fenced code block.
    (function addCopyButtons() {
      var COPY_ICON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>';
      var CHECK_ICON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>';
      document.querySelectorAll('#content pre').forEach(function (pre) {
        var wrap = document.createElement('div');
        wrap.className = 'code-block';
        // Single-line blocks center the button vertically; multi-line keep it top-right.
        if (pre.textContent.replace(/\\n$/, '').indexOf('\\n') === -1) {
          wrap.className += ' code-block--single';
        }
        pre.parentNode.insertBefore(wrap, pre);
        wrap.appendChild(pre);

        var btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.type = 'button';
        btn.title = 'Copy to clipboard';
        btn.setAttribute('aria-label', 'Copy to clipboard');
        btn.innerHTML = COPY_ICON;
        wrap.appendChild(btn);

        var timer;
        btn.addEventListener('click', function () {
          navigator.clipboard.writeText(pre.textContent).then(function () {
            btn.innerHTML = CHECK_ICON;
            clearTimeout(timer);
            timer = setTimeout(function () { btn.innerHTML = COPY_ICON; }, 2000);
          });
        });
      });
    })();
  </script>
</body>
</html>
"""


def main() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    if "</script>" in readme:
        raise SystemExit("README.md contains </script>; cannot inline safely.")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(TEMPLATE.replace("__README__", readme), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
