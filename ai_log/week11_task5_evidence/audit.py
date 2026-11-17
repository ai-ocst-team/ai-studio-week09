"""Reproduce the scoped Week 11 Task 5 audit; does not commit or send CSV data."""
from __future__ import annotations

import ast
from datetime import datetime, timezone, timedelta
from io import BytesIO
from pathlib import Path
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    print('Audit time:', datetime.now(timezone(timedelta(hours=9))).isoformat())
    print('Python:', sys.version.split()[0])
    for package in ('pandas', 'pillow', 'pytest'):
        print(package, importlib.metadata.version(package))
    def git(*args: str) -> str:
        p = subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8')
        print('git', json.dumps(args), 'exit=', p.returncode)
        if p.stdout.strip():
            print(p.stdout.strip())
        else:
            print('(no output)')
        if p.returncode:
            raise RuntimeError('Git audit command failed: ' + ' '.join(args))
        return p.stdout
    git('rev-parse', 'HEAD')
    git('rev-parse', '--is-shallow-repository')
    tracked = git('ls-files', '--', '.env*', '**/.env*')
    history = git('log', '--all', '--full-history', '--format=%h %s', '--', '**.env*', '.env*', '**/.env*')
    if tracked.strip() or history.strip():
        raise RuntimeError('Environment file paths found; review required')
    probes = ['.env', 'nested/.env', '.env.production', 'nested/.env.local', '.venv/probe', '__pycache__/probe', 'test.local']
    ignored = git('check-ignore', '--', *probes).splitlines()
    if set(ignored) != set(probes):
        raise RuntimeError('Some environment/cache probes are not ignored')

    app_source = (ROOT/'app.py').read_text(encoding='utf-8-sig')
    app = ast.parse(app_source)
    backend_source = (ROOT/'backend.py').read_text(encoding='utf-8-sig')
    backend = ast.parse(backend_source)
    forbidden = {'groupby', 'to_datetime', 'clip', 'explode', 'dropna', 'fillna', 'mean'}
    calls = [n for n in ast.walk(app) if isinstance(n, ast.Call)]
    mixed = [(n.lineno, n.func.attr) for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr in forbidden]
    imports = [ast.unparse(n) for n in ast.walk(backend) if isinstance(n, (ast.Import, ast.ImportFrom))]
    print('UI transformation calls:', mixed)
    print('backend imports:', imports)
    if mixed or any('streamlit' in s for s in imports):
        raise RuntimeError('UI/backend separation requires review')
    for key in ('prepared_df', 'uploaded_file_sig'):
        if f'if "{key}" not in st.session_state:' not in app_source:
            raise RuntimeError('Missing guarded session initialization')
    print('Session initialization guards: present; file replacement/error reset: reviewed in source')

    # Execute only the unchanged CSV reader AST, not Streamlit UI or a recreated reader.
    import pandas as pd
    from backend import prepare_uploaded_dataframe, summarize_photo_dashboard, validate_columns, filter_analyses
    node = next(n for n in app.body if isinstance(n, ast.FunctionDef) and n.name == '_read_csv_with_cp949_fallback')
    scope = {'pd': pd}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'app.py', 'exec'), scope)
    reader = scope[node.name]
    summaries = []
    for name in ('sample_photos.csv', 'sample_photos_cp949.csv'):
        data = (ROOT/'sample_data'/name).read_bytes()
        if 'cp949' in name:
            try:
                data.decode('utf-8')
            except UnicodeDecodeError:
                print('CP949 sample fails UTF-8 as expected')
            else:
                raise RuntimeError('CP949 fallback not exercised')
        df = prepare_uploaded_dataframe(reader(BytesIO(data)))
        summary = summarize_photo_dashboard(df)
        compact = {k: summary[k] for k in ('total_photos', 'avg_score', 'valid_date_count')}
        summaries.append(compact)
        print(name, json.dumps(compact), 'month_rows=', len(summary['monthly_df']), 'tag_rows=', len(summary['tags_df']))
        filtered = summarize_photo_dashboard(filter_analyses(df, selected_tag='건축도시'))
        print('architecture tag filter:', filtered['total_photos'], filtered['avg_score'])
    if summaries[0] != summaries[1]:
        raise RuntimeError('Encoding results differ')
    broken = reader(BytesIO((ROOT/'sample_data/sample_photos_broken.csv').read_bytes()))
    print('Broken CSV missing:', validate_columns(broken))
    try:
        prepare_uploaded_dataframe(broken)
    except ValueError as e:
        print('Broken CSV rejected:', str(e))
    else:
        raise RuntimeError('Broken CSV accepted')

    files = ['app.py', 'backend.py', 'clean_analysis_dataframe/clean_analysis_dataframe.py', 'aggregate_photo_insights/photo_analytics.py', 'sample_data/generate_samples.py']
    # Literal credential and explicit external-call heuristics, never print candidate values.
    credential = re.compile(r'''(?i)(?:api[_-]?key|password|secret|token)\s*=\s*["'][^"']{8,}["']''')
    transport = re.compile(r'\b(?:requests|httpx|urllib|openai|genai|socket|subprocess)\b|\beval\s*\(')
    hits = []
    for f in files:
        for line, value in enumerate((ROOT/f).read_text(encoding='utf-8-sig').splitlines(), 1):
            if credential.search(value) or transport.search(value):
                hits.append((f, line))
    print('Scoped credential/transport heuristic locations (values suppressed):', hits)
    print('Scope limit: no full-history secret-content scan, image OCR, external account audit or browser interaction.')

    # A fresh temporary parent prevents pytest basetemp from touching existing data.
    with tempfile.TemporaryDirectory(prefix='week11-audit-', dir=ROOT.parent) as temp:
        args = [sys.executable, '-B', '-X', 'utf8', '-m', 'pytest', '-q', '-o', 'addopts=', '-p', 'no:cacheprovider', '--basetemp=' + str(Path(temp)/'pytest')]
        print('Test command:', json.dumps(args), flush=True)
        env = os.environ.copy()
        env.pop('USE_MOCK', None)
        result = subprocess.run(args, env=env, capture_output=True, text=True, encoding='utf-8')
        print(result.stdout, result.stderr)
        print('pytest_exit_code=', result.returncode)
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
