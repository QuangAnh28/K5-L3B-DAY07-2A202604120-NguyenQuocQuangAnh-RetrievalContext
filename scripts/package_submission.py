"""Create a local submission archive from explicit public directories only."""
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.common import load,save,digest
from dotenv import dotenv_values

def main():
    directories=['src','starter','tests','docs','assets','benchmark','data','report','results','scripts']
    files=[p for p in ROOT.glob('*.md')]
    files += [ROOT/n for n in ['requirements.txt','requirements-lock.txt','.gitignore','.gitattributes','.env.example']]
    for name in directories:
        for p in (ROOT/name).rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(ROOT)
            if '__pycache__' in rel.parts:continue
            if name=='starter' and any(part in ('data','results','.venv') for part in rel.parts[1:]):continue
            if p.name=='.env' or p.suffix in ('.pyc','.pyo'):continue
            files.append(p)
    files += [ROOT/'artifacts/day6-reuse.zip',ROOT/'artifacts/day6-reuse-manifest.json',
              ROOT/'artifacts/bonus-reuse.zip',ROOT/'artifacts/bonus-reuse-manifest.json']
    files=sorted(set(files))
    secret_values=[str(v).encode() for k,v in dotenv_values(ROOT/'.env').items()
                   if any(s in k for s in ['KEY','TOKEN','PASSWORD']) and v and len(v)>10]
    for p in files:
        if p.suffix=='.zip':
            with zipfile.ZipFile(p) as z:
                contents=[z.read(n) for n in z.namelist()]
        else:contents=[p.read_bytes()]
        if any(secret in data for secret in secret_values for data in contents):
            raise RuntimeError('Credential found in submission; no archive written')
    out=ROOT/'artifacts/K5-L3B-DAY07-2A202604120-NguyenQuocQuangAnh.zip'
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    save(ROOT/'artifacts/submission-manifest.json',{'archive':out.name,'sha256':digest(out),
        'files':len(files),'bytes':out.stat().st_size,'local_credential_scan_passed':True,
        'excluded':['.env','.git','.venv','.day6','.bonus','original Day 6 ZIP','original FPT PDF and full-page images'],
        'note':'Sanitized Day 6 and FPT vector snapshots included; model credentials supplied locally, original FPT PDF required to restore page images.'})
    print('Submission archive:',out.name,'files:',len(files),'bytes:',out.stat().st_size)

if __name__=='__main__':main()
