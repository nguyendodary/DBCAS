import { useMemo, useRef } from 'react'

const KEYWORDS = new Set(('select from where join inner left right full outer cross on as distinct group by having order asc desc limit offset union all intersect except with recursive exists in not and or is null true false case when then else end over partition rows range between current row preceding following filter returning insert into values update delete create table alter drop primary foreign key references constraint check unique default').split(' '))
const FUNCTIONS = new Set(('count sum avg min max coalesce nullif cast round lower upper length substring concat extract date_trunc row_number rank dense_rank lag lead').split(' '))
const TOKENS = /--[^\r\n]*|\/\*[\s\S]*?(?:\*\/|$)|'(?:''|[^'])*(?:'|$)|"(?:""|[^"])*(?:"|$)|(\$(?:[a-zA-Z_]\w*)?\$)[\s\S]*?\1|\b\d+(?:\.\d+)?(?:e[+-]?\d+)?\b|\b[a-zA-Z_]\w*\b|[<>=!+*/%-]+/gi

// Presentation-only lexer. Plain text spans never interpret SQL as markup.
export function sqlTokens(value) {
  const result = []
  let position = 0
  for (const match of value.matchAll(TOKENS)) {
    if (match.index > position) result.push({ text: value.slice(position, match.index) })
    const text = match[0]
    const word = text.toLowerCase()
    const kind = text.startsWith('--') || text.startsWith('/*') ? 'comment'
      : text.startsWith("'") || text.startsWith('$') ? 'string'
        : text.startsWith('"') ? 'identifier'
          : /^\d/.test(text) ? 'number'
            : KEYWORDS.has(word) ? 'keyword' : FUNCTIONS.has(word) ? 'function' : ''
    result.push({ text, kind })
    position = match.index + text.length
  }
  result.push({ text: value.slice(position) })
  return result
}

export default function SqlEditor({ value, onChange, disabled = false }) {
  const highlightRef = useRef(null)
  const tokens = useMemo(() => sqlTokens(value), [value])
  return <div className="sql-editor relative min-w-0 overflow-hidden bg-abyss focus-within:ring-2 focus-within:ring-inset focus-within:ring-cyan-400/50">
    <pre ref={highlightRef} aria-hidden="true" className="sql-highlight pointer-events-none absolute inset-0 m-0 overflow-hidden whitespace-pre p-4 font-mono text-sm leading-6 text-ink">
      {tokens.map((token, index) => <span key={index} className={token.kind ? `sql-${token.kind}` : undefined}>{token.text}</span>)}{'\n'}
    </pre>
    <textarea aria-label="Your query" aria-describedby="sql-editor-help" value={value} onChange={(e) => onChange(e.target.value)}
      onScroll={(e) => { highlightRef.current.scrollTop = e.currentTarget.scrollTop; highlightRef.current.scrollLeft = e.currentTarget.scrollLeft }}
      disabled={disabled} maxLength={16000} rows={12} wrap="off" spellCheck={false} autoCapitalize="off" autoCorrect="off"
      className="sql-input relative block min-h-72 w-full resize-y bg-transparent p-4 font-mono text-sm leading-6 focus:outline-none"
      placeholder="SELECT ..." />
    <span id="sql-editor-help" className="sr-only">SQL syntax is highlighted. Use the schema viewer to inspect available tables. Tab moves to the next control.</span>
  </div>
}
