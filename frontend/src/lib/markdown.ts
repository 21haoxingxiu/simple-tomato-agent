/**
 * 轻量 Markdown 渲染(不引入额外依赖)。
 * 支持: 标题 / 粗体 / 斜体 / 行内代码 / 代码块 / 列表 / 链接 / 引用角标。
 * 输出 HTML 字符串,所有用户输入做 escape。
 */
export function renderMarkdown(input: string): string {
  if (!input) return ""
  let text = escapeHtml(input)

  // fenced code blocks
  text = text.replace(/```([a-zA-Z0-9_+\-]*)?\n([\s\S]*?)```/g, (_m, lang, code) => {
    return `<pre class="md-code"><code data-lang="${lang || ""}">${code.replace(/\n$/, "")}</code></pre>`
  })

  // headings
  text = text.replace(/^######\s+(.*)$/gm, "<h6>$1</h6>")
  text = text.replace(/^#####\s+(.*)$/gm, "<h5>$1</h5>")
  text = text.replace(/^####\s+(.*)$/gm, "<h4>$1</h4>")
  text = text.replace(/^###\s+(.*)$/gm, "<h3>$1</h3>")
  text = text.replace(/^##\s+(.*)$/gm, "<h2>$1</h2>")
  text = text.replace(/^#\s+(.*)$/gm, "<h1>$1</h1>")

  // blockquote
  text = text.replace(/^&gt;\s+(.*)$/gm, "<blockquote>$1</blockquote>")

  // bold / italic / inline code
  text = text.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
  text = text.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
  text = text.replace(/`([^`\n]+)`/g, "<code>$1</code>")

  // citations like [1] [2]
  text = text.replace(/\[(\d+)\]/g, '<sup class="md-cite" data-idx="$1">[$1]</sup>')

  // links [t](u)
  text = text.replace(
    /\[([^\]]+)\]\((https?:[^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
  )

  // simple lists
  text = text.replace(/(^|\n)(- |\* )(.*)(?=\n|$)/g, (_m, p1, _b, item) => {
    return `${p1}<li>${item}</li>`
  })
  text = text.replace(/(<li>[\s\S]+?<\/li>)/g, (block) => {
    if (block.includes("</ul>")) return block
    return `<ul>${block}</ul>`
  })
  text = text.replace(/<\/ul>\s*<ul>/g, "")

  // paragraphs (avoid wrapping block tags)
  text = text
    .split(/\n{2,}/)
    .map((para) => {
      if (/^\s*<(h\d|ul|pre|blockquote|li)/.test(para.trim())) return para
      return `<p>${para.replace(/\n/g, "<br/>")}</p>`
    })
    .join("\n")

  return text
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
}
