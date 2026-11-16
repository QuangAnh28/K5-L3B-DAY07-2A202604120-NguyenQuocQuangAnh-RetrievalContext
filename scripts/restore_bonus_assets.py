"""Recreate local original-page images without changing frozen corpus metadata."""
import argparse
from pathlib import Path
import shutil
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.common import load,digest

def restore(pdf,snapshot=None):
    import pypdfium2 as pdfium
    manifest=load(ROOT/'data/bonus/manifest.json')
    if digest(pdf)!=manifest['pdf_sha256']:raise ValueError('PDF SHA256 differs from the benchmark source version')
    local=ROOT/'.bonus';local.mkdir(exist_ok=True)
    target=local/'BCTN-2025.pdf'
    if not target.exists():shutil.copyfile(pdf,target)
    if digest(target)!=manifest['pdf_sha256']:raise ValueError('Existing local PDF differs')
    document=pdfium.PdfDocument(str(target));pages=load(ROOT/'data/bonus/pages.json')
    if len(document)!=len(pages):raise ValueError('Page coverage mismatch')
    for info in pages:
        dest=ROOT/info['image'];dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():
            page=document[info['page']-1];width,height=page.get_size();bitmap=page.render(scale=1600/width)
            bitmap.to_pil().convert('RGB').save(dest,quality=90);bitmap.close();page.close()
        if digest(dest)!=info['image_sha256']:raise ValueError('Rendered page hash mismatch: '+info['id'])
    document.close()
    if snapshot:
        allowed={'qdrant/meta.json','qdrant/collection/FPT2025/storage.sqlite','embedding_cache.json'}
        with zipfile.ZipFile(snapshot) as z:
            if set(z.namelist())!=allowed:raise ValueError('Unexpected snapshot files')
            for name in allowed:
                if (local/name).exists():raise ValueError('Local vector files exist; refusing overwrite')
            for name in allowed:
                dest=local/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
    print('Restored/verified all',len(pages),'original page images. Frozen corpus files unchanged.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pdf',required=True,type=Path);p.add_argument('--snapshot',type=Path)
    a=p.parse_args();restore(a.pdf,a.snapshot)
