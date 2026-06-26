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
