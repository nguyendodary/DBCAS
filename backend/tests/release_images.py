"""Smoke actual release images on owned networks and memory-only databases.

No user database, provider credentials or existing container is used. Secrets
are generated in memory and neither subprocess arguments nor logs are printed.
"""
import json
import os
from pathlib import Path
import secrets
import subprocess
import shutil
import time
from urllib.parse import quote
import uuid
import httpx
import ipaddress

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT.parent / '_review/remediation'
BACKEND_IMAGE = os.environ.get('DBCAS_RELEASE_BACKEND_IMAGE', 'dbcas-release-backend:local')
FRONTEND_IMAGE = os.environ.get('DBCAS_RELEASE_FRONTEND_IMAGE', 'dbcas-release-frontend:local')
SANDBOX_IMAGE = os.environ.get('DBCAS_RELEASE_SANDBOX_IMAGE', 'dbcas-sandbox-test')
RELEASE_REVISION = os.environ.get('DBCAS_RELEASE_REVISION')


def main():
    run_id = uuid.uuid4().hex[:10]
    prefix = 'dbcas-image-gate-' + run_id
    containers, networks = [], []
    redactions = []
    label = 'dbcas.image-gate=' + run_id
    executable = shutil.which('docker') or 'docker'
    cli = ['wsl.exe', '-e', 'docker'] if os.name == 'nt' and executable.lower().endswith('.cmd') else [executable]
    def docker(*args, input=None, allow_failure=False):
        result = subprocess.run([*cli, *args], input=input, capture_output=True, timeout=180)
        if result.returncode and not allow_failure:
            error = 'Docker exit code: ' + str(result.returncode) + '\n' + (result.stdout + result.stderr).decode(errors='replace')
            for secret in sorted(redactions, key=len, reverse=True):
                error = error.replace(secret, '[redacted]')
            ARTIFACTS.mkdir(parents=True, exist_ok=True)
            (ARTIFACTS / ('image-gate-error-' + run_id + '.txt')).write_text(error, encoding='utf-8')
            raise RuntimeError('Release image gate Docker operation failed; no command or secret was printed')
        return result
    def network(suffix, internal=False):
        name = prefix + '-' + suffix
        # Small explicit test subnets avoid consuming Docker's default /16
        # pool. Refuse overlap rather than deleting unrelated networks.
        subnet = ipaddress.ip_network(f'10.231.240.{len(networks) * 16}/28')
        ids = docker('network', 'ls', '-q').stdout.decode().split()
        existing = json.loads(docker('network', 'inspect', *ids).stdout)
        used = [ipaddress.ip_network(config['Subnet']) for net in existing
            for config in (net.get('IPAM', {}).get('Config') or []) if config.get('Subnet') and ':' not in config['Subnet']]
        if any(subnet.overlaps(other) for other in used):
            raise RuntimeError('Reserved image-gate subnet overlaps an existing Docker network')
        docker('network', 'create', '--label', label, '--subnet', str(subnet), *(['--internal'] if internal else []), name)
        networks.append(name)
        return name
    def launch(suffix, image, net, alias, env=None, extra=()):
        name = prefix + '-' + suffix
        args = ['run', '-d', '--label', label, '--name', name, '--network', net, '--network-alias', alias]
        for key, value in (env or {}).items():
            args.extend(['-e', key + '=' + value])
        docker(*args, *extra, image)
        containers.append(name)
        return name
    def port(name, target):
        return int(docker('port', name, str(target) + '/tcp').stdout.decode().strip().rsplit(':', 1)[1])
    def wait_database(name, database):
        for _ in range(60):
            if docker('exec', name, 'pg_isready', '-h', '127.0.0.1', '-U', 'postgres', '-d', database, allow_failure=True).returncode == 0:
                # Force TCP readiness beyond the image's temporary init server.
                return
            time.sleep(1)
        raise RuntimeError('Image gate database startup timed out')
    report = {'images': {}}
    try:
        for component, image in (('backend', BACKEND_IMAGE), ('frontend', FRONTEND_IMAGE), ('sandbox', SANDBOX_IMAGE)):
            details = json.loads(docker('image', 'inspect', image).stdout)[0]
            revision = (details.get('Config', {}).get('Labels') or {}).get('org.opencontainers.image.revision')
            if RELEASE_REVISION and revision != RELEASE_REVISION:
                raise RuntimeError(f'{component} release image revision does not match the requested revision')
            report['images'][component] = {'reference': image, 'revision': revision}
        app_net, sql_net, web_net = network('app', True), network('sql', True), network('web')
        db_pass, sql_admin_pass = secrets.token_hex(24), secrets.token_hex(24)
        sql_learner_pass = secrets.token_hex(24) + "'quoted"
        redactions.extend([db_pass, sql_admin_pass, sql_learner_pass, quote(sql_learner_pass, safe='')])
        db = launch('db', 'postgres:17', app_net, 'db', {'POSTGRES_PASSWORD': db_pass, 'POSTGRES_DB': 'dbcas'},
            ('--tmpfs', '/var/lib/postgresql/data:rw,size=256m'))
        sandbox = launch('sandbox', SANDBOX_IMAGE, sql_net, 'sandbox',
            {'POSTGRES_PASSWORD': sql_admin_pass, 'SANDBOX_LEARNER_PASSWORD': sql_learner_pass},
            ('--tmpfs', '/var/lib/postgresql/data:rw,size=256m', '--memory', '256m', '--cpus', '1', '--pids-limit', '200'))
        wait_database(db, 'dbcas')
        wait_database(sandbox, 'postgres')
        sql_result = docker('exec', '-e', 'PGPASSWORD=' + sql_learner_pass, sandbox, 'psql',
            '-h', '127.0.0.1', '-v', 'ON_ERROR_STOP=1', '-U', 'learner_ro', '-d', 'postgres',
            '-Atc', 'SELECT 1 AS release_image_smoke')
        if sql_result.stdout.decode().strip() != '1':
            raise RuntimeError('Release sandbox safe SELECT returned an unexpected result')
        report['safe_sql_sandbox_select'] = 'PASS'
        docker('exec', '-i', db, 'psql', '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', 'dbcas', input=(ROOT / 'db/schema.sql').read_bytes())
        env = {'DEPLOYMENT_MODE': 'production', 'JWT_SECRET': secrets.token_hex(32),
            'DATABASE_URL': f'postgresql://postgres:{db_pass}@db:5432/dbcas',
            'SANDBOX_ADMIN_URL': f'postgresql://postgres:{sql_admin_pass}@sandbox:5432/postgres',
            'SANDBOX_URL': f'postgresql://learner_ro:{quote(sql_learner_pass, safe="")}@sandbox:5432/postgres',
            'FRONTEND_URL': 'https://dbcas.test', 'CORS_ORIGINS': '["https://dbcas.test"]',
            'LLM_API_KEY': '', 'GOOGLE_CLIENT_ID': '', 'GITHUB_CLIENT_ID': ''}
        redactions.extend(value for key, value in env.items() if key in ('JWT_SECRET', 'DATABASE_URL', 'SANDBOX_URL', 'SANDBOX_ADMIN_URL'))
        args = [item for key, value in env.items() for item in ('-e', key + '=' + value)]
        migration = docker('run', '--rm', '--label', label, '--network', app_net, *args,
            BACKEND_IMAGE, 'python', '-m', 'app.migrate')
        report['migration_command'] = 'PASS'
        unsafe = docker('run', '--rm', '--label', label, '--network', app_net, *args,
            '-e', 'JWT_SECRET=change_me_jwt_secret', BACKEND_IMAGE,
            'python', '-c', 'from app.config import Settings; Settings()', allow_failure=True)
        if unsafe.returncode == 0:
            raise RuntimeError('Unsafe production secret was accepted')
        report['unsafe_production_secret_rejected'] = True
        api = launch('backend', BACKEND_IMAGE, app_net, 'backend', env,
            ('-p', '127.0.0.1:0:8000'))
        docker('network', 'connect', sql_net, api)
        docker('network', 'connect', '--alias', 'backend', web_net, api)
        base = 'http://127.0.0.1:' + str(port(api, 8000))
        for _ in range(60):
            try:
                ready = httpx.get(base + '/readiness', timeout=5)
                if ready.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(1)
        else:
            raise RuntimeError('Release image readiness did not pass')
        report['readiness'] = ready.json()
        report['sandbox_password_with_quote'] = 'PASS'
        with httpx.Client(base_url=base, timeout=15) as client:
            password = secrets.token_hex(16)
            registered = client.post('/api/v1/auth/register', json={'email': 'image-gate@test.dev',
                'password': password, 'password_confirm': password, 'name': 'Disposable image gate'})
            registered.raise_for_status()
            assert client.get('/api/v1/auth/oauth/providers').status_code == 200
            login = client.post('/api/v1/auth/login', json={'email': 'image-gate@test.dev', 'password': password})
            login.raise_for_status()
            token = login.json()['access_token']
            headers = {'Authorization': 'Bearer ' + token}
            me = client.get('/api/v1/auth/me', headers=headers)
            me.raise_for_status()
            assert me.json().get('account_id')
            assessment_list = client.get('/api/v1/assessments', headers=headers)
            assessment_list.raise_for_status()
        report['registration'] = 'PASS'
        report['login'] = 'PASS'
        report['learner_read'] = {'auth_me': 'PASS', 'assessment_list': 'PASS', 'assessment_count': len(assessment_list.json())}
        ui = launch('frontend', FRONTEND_IMAGE, web_net, 'frontend', extra=('-p', '127.0.0.1:0:8080'))
        ui_base = 'http://127.0.0.1:' + str(port(ui, 8080))
        with httpx.Client(base_url=ui_base, timeout=10) as client:
            for _ in range(30):
                try:
                    page = client.get('/login')
                    if page.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            else:
                raise RuntimeError('Release frontend startup timed out')
            assert client.get('/admin/questions').status_code == 200
            assert client.get('/readiness').status_code == 200
            assert 'Content-Security-Policy' in page.headers
            assert page.headers.get('X-Content-Type-Options') == 'nosniff'
        # A separate Chromium context inspects production assets, CSP and fonts.
        node = r'''
const { chromium } = require('./frontend/node_modules/playwright');
(async () => {
 const browser = await chromium.launch(); const page = await browser.newPage();
 const errors = []; page.on('pageerror', e => errors.push(e.message));
 const started = Date.now(); await page.goto(process.env.DBCAS_GATE_UI + '/login');
 await page.getByRole('heading', { name: 'Sign in to DBCAS' }).waitFor();
 const readyMs = Date.now() - started;
 await page.evaluate(() => document.fonts.ready);
 const fonts = await page.evaluate(() => document.fonts.check('16px "Plus Jakarta Sans Variable"'));
 await page.screenshot({path: process.env.DBCAS_GATE_SCREENSHOT, fullPage: true});
 console.log(JSON.stringify({login_ready_ms: readyMs, local_fonts_loaded: fonts, runtime_errors: errors}));
 await browser.close(); if(errors.length || !fonts || readyMs > 1500) process.exit(1);
})().catch(() => { console.error('Production browser gate failed'); process.exit(1) });
'''
        measured = subprocess.run(['node', '-e', node], cwd=ROOT, env={**os.environ,
            'DBCAS_GATE_UI': ui_base, 'DBCAS_GATE_SCREENSHOT': str(ARTIFACTS / 'screenshots/login-production-1280.png')},
            capture_output=True, timeout=60)
        if measured.stdout:
            report['production_browser'] = json.loads(measured.stdout)
        if measured.returncode:
            (ARTIFACTS / 'release-images-browser-failed.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            raise RuntimeError('Production browser page gate failed; aggregate measurement retained')
        report['python'] = docker('run', '--rm', BACKEND_IMAGE, 'python', '--version').stdout.decode().strip()
        report['frontend_proxy_security_headers'] = 'PASS'
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        (ARTIFACTS / 'release-images.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
    finally:
        for name in reversed(containers):
            inspected = docker('inspect', name, allow_failure=True)
            if inspected.returncode == 0 and json.loads(inspected.stdout)[0]['Config']['Labels'].get('dbcas.image-gate') == run_id:
                docker('rm', '-f', name)
        for name in reversed(networks):
            inspected = docker('network', 'inspect', name, allow_failure=True)
            if inspected.returncode == 0 and json.loads(inspected.stdout)[0]['Labels'].get('dbcas.image-gate') == run_id:
                docker('network', 'rm', name)


if __name__ == '__main__':
    main()
