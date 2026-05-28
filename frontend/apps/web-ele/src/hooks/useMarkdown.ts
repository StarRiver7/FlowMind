import { marked } from 'marked';
import hljs from 'highlight.js';

// Configure marked with highlight.js
marked.setOptions({
  breaks: true,
  gfm: true,
  highlight(code: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value;
      } catch { /* fall through */ }
    }
    try {
      return hljs.highlightAuto(code).value;
    } catch {
      return code;
    }
  },
});

/**
 * Render markdown string to HTML with citation [n] placeholders preserved.
 * Citations like [1], [2,3] are rendered as clickable superscript badges.
 */
export function renderMarkdown(text: string): string {
  if (!text) return '';
  // Replace citation markers [n] or [n,m] with HTML badges before markdown rendering
  const withCitations = text.replace(
    /\[(\d+(?:,\d+)*)\]/g,
    (_: string, nums: string) => {
      const ids = nums.split(',').map((n: string) => n.trim());
      return ids.map((id: string) =>
        `<sup class="isu-citation" data-cite="${id}">${id}</sup>`
      ).join('');
    }
  );
  return marked.parse(withCitations) as string;
}

/**
 * Strip markdown for plain text preview (e.g. conversation title)
 */
export function stripMarkdown(text: string): string {
  return text
    .replace(/[#*`~\[\]()>]/g, '')
    .replace(/\n+/g, ' ')
    .trim()
    .slice(0, 80);
}

export function useMarkdown() {
  return { renderMarkdown, stripMarkdown };
}
