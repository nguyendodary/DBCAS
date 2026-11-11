// Loopback-only OAuth fixture. No Google/GitHub network access or live keys.
import { createServer } from 'node:http'
import { createHash, randomUUID } from 'node:crypto'
import { URL, URLSearchParams } from 'node:url'
import process from 'node:process'

const origin = 'http://127.0.0.1:8101'
const web = 'http://127.0.0.1:5174'
const codes = new Map()
const tokens = new Map()
const hash = (value) => createHash('sha256').update(value).digest('hex')
const escape = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (c) =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      })[c],
  )

const server = createServer(async (request, response) => {
  const url = new URL(request.url, origin)
  const send = (status, body) => {
    response.writeHead(status, { 'content-type': 'application/json', 'cache-control': 'no-store' })
    response.end(JSON.stringify(body))
  }
  if (url.pathname === '/health') return send(200, { fixture: 'local-oauth' })
  const [, provider, action] = url.pathname.split('/')
  if (!['google', 'github'].includes(provider)) return send(404, {})
  const callback = `${web}/api/v1/auth/oauth/${provider}/callback`
  if (action === 'authorize') {
    if (
      url.searchParams.get('redirect_uri') !== callback ||
      url.searchParams.get('client_id') !== `dbcas-e2e-${provider}-client` ||
      !url.searchParams.get('state')
    )
      return send(400, { error: 'invalid_request' })
    const hidden = [...url.searchParams]
      .map(
        ([name, value]) => `<input type="hidden" name="${escape(name)}" value="${escape(value)}">`,
      )
      .join('')
    response.writeHead(200, { 'content-type': 'text/html', 'cache-control': 'no-store' })
    response.end(`<!doctype html><html lang="en"><title>Local fake ${provider}</title><main>
      <h1>Local fake ${provider}</h1><form action="/${provider}/consent">
      ${hidden}<label>Email <input name="email" type="email" required value="fake@test.dev"></label>
      <button name="decision" value="accept">Accept verified email</button>
      <button name="decision" value="denied">Deny consent</button>
      <button name="decision" value="unverified">Use unverified email</button>
      <button name="decision" value="down">Provider unavailable</button></form></main></html>`)
    return
  }
  if (action === 'consent') {
    if (url.searchParams.get('redirect_uri') !== callback) return send(400, {})
    const target = new URL(callback)
    target.searchParams.set('state', url.searchParams.get('state') || '')
    if (url.searchParams.get('decision') === 'denied')
      target.searchParams.set('error', 'access_denied')
    else {
      const code = randomUUID()
      codes.set(code, {
        provider,
        email: (url.searchParams.get('email') || '').toLowerCase(),
        verified: url.searchParams.get('decision') !== 'unverified',
        down: url.searchParams.get('decision') === 'down',
        challenge: url.searchParams.get('code_challenge'),
      })
      target.searchParams.set('code', code)
    }
    response.writeHead(302, { location: target.href, 'cache-control': 'no-store' })
    response.end()
    return
  }
  if (action === 'token' && request.method === 'POST') {
    let body = ''
    for await (const chunk of request) body += chunk
    const params = new URLSearchParams(body)
    const identity = codes.get(params.get('code'))
    codes.delete(params.get('code'))
    if (
      !identity ||
      identity.provider !== provider ||
      params.get('redirect_uri') !== callback ||
      params.get('client_id') !== `dbcas-e2e-${provider}-client` ||
      params.get('client_secret') !== 'test-only-no-provider-access'
    )
      return send(400, { error: 'invalid_grant' })
    if (
      provider === 'google' &&
      createHash('sha256')
        .update(params.get('code_verifier') || '')
        .digest('base64url') !== identity.challenge
    )
      return send(400, { error: 'invalid_pkce' })
    if (identity.down) return send(503, { error: 'temporarily_unavailable' })
    const token = randomUUID()
    tokens.set(token, identity)
    return send(200, { access_token: token, token_type: 'bearer' })
  }
  const identity = tokens.get((request.headers.authorization || '').replace(/^Bearer /i, ''))
  if (!identity || identity.provider !== provider) return send(401, {})
  if (action === 'userinfo')
    return send(200, {
      sub: `${provider}-${hash(identity.email)}`,
      email: identity.email,
      email_verified: identity.verified,
      name: 'Local OAuth learner',
    })
  if (action === 'user')
    return send(200, {
      id: parseInt(hash(identity.email).slice(0, 12), 16),
      login: 'local-learner',
      name: 'Local OAuth learner',
    })
  if (action === 'emails')
    return send(200, [{ email: identity.email, verified: identity.verified, primary: true }])
  return send(404, {})
})
server.listen(8101, '127.0.0.1')
for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, () => server.close())
