"""Restore the supplied Windows Day 6 dependencies and credentials locally.

Use only with the user's trusted archive. Nothing under .git is imported.
For another OS/Python version install requirements.txt into a fresh venv instead.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import zipfile

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--zip',type=Path,required=True)
    parser.add_argument('--restore-deps',action='store_true',help='Same Windows/Python ABI as Day 6 only')
    parser.add_argument('--import-key',action='store_true',help='Copy only OpenRouter key/model into ignored .env')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    with zipfile.ZipFile(args.zip) as z:
        prefix=z.namelist()[0].split('/')[0]+'/'
        if args.restore_deps:
            if sys.platform!='win32' or sys.version_info[:2]!=(3,14):
                raise RuntimeError('Bundled native dependencies require Windows CPython 3.14')
            subprocess.run([sys.executable,'-m','venv',str(root/'.venv')],check=True)
            site=root/'.venv/Lib/site-packages'
            start=prefix+'starter/.venv/Lib/site-packages/'
            for info in z.infolist():
                if not info.is_dir() and info.filename.startswith(start):
                    target=site/info.filename[len(start):]
                    if not target.resolve().is_relative_to(site.resolve()):
                        raise ValueError('Unsafe archive path')
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(z.read(info))
        if args.import_key:
            settings={}
            for line in z.read(prefix+'starter/.env').decode('utf-8-sig').splitlines():
                if '=' in line and not line.startswith('#'):
                    key,value=line.split('=',1)
                    if key.strip() in ('OPENROUTER_API_KEY','EMBEDDING_MODEL'):
                        settings[key.strip()]=value.strip()
            path=root/'.env'
            if path.exists():
                print('Existing .env preserved.')
            else:
                path.write_text('\n'.join(k+'='+v for k,v in settings.items())+'\nAGENT_MODEL=openai/gpt-4.1-mini\n',encoding='utf-8')
                print('Local .env created; credentials not printed.')
    print('Bootstrap complete. Import corpus with python -m src.prepare --zip <archive>.')

if __name__=='__main__':main()
