"""Package new website source and byte-identical research archives. No research edits."""
import argparse, hashlib, json, shutil, zipfile
from pathlib import Path

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()

def source_files(root):
    excluded = {'node_modules','.venv','.next','.git','__pycache__','.pytest_cache','test-results'}
    for p in sorted(root.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(root)
        if any(x in excluded for x in rel.parts): continue
        if rel.parts[0] in {'data','incoming'} and p.name!='.gitkeep': continue
        if '.local.' in p.name or p.name.endswith(('.tsbuildinfo','.zip')): continue
        if p.name=='qa-responsive.html': continue
        yield p, rel

def main():
    parser=argparse.ArgumentParser()
    for name in ['website','research-zip','editorial-zip','snapshot-root','output-dir']: parser.add_argument('--'+name,required=True,type=Path)
    a=parser.parse_args();out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    stage=out/'SUMAFIRE_INSIGHT_Paket_Lengkap_F1E325063';stage.mkdir(exist_ok=True)
    web=stage/'sumafire-insight'
    for p,r in source_files(a.website):
        target=web/r;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    assert (web/'src/app/api/data/route.ts').is_file()
    assert not (web/'data/active.json').exists()
    archives=stage/'research_original';archives.mkdir(exist_ok=True)
    archive_manifest=[]
    for source in [a.research_zip,a.editorial_zip]:
        target=archives/source.name;shutil.copy2(source,target)
        assert digest(source)==digest(target)
        archive_manifest.append({'file':str(target.relative_to(stage)),'bytes':target.stat().st_size,'sha256':digest(target),'byte_identical':True})
    sid=json.loads((a.snapshot_root/'active.json').read_text())['snapshot'];snap=stage/'prepared_snapshot';snap.mkdir(exist_ok=True)
    shutil.copy2(a.snapshot_root/'active.json',snap/'active.json');shutil.copytree(a.snapshot_root/'processed'/sid,snap/'processed'/sid,dirs_exist_ok=True)
    (stage/'ARCHIVE_MANIFEST.json').write_text(json.dumps(archive_manifest,indent=2))
    if (a.website/'docs/MULAI_DISINI.md').is_file():shutil.copy2(a.website/'docs/MULAI_DISINI.md',stage/'MULAI_DISINI.md')
    for name,folder in [('SUMAFIRE_INSIGHT_Source_Code.zip',web),('SUMAFIRE_INSIGHT_Paket_Lengkap_F1E325063.zip',stage)]:
        target=out/name
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(folder.rglob('*')):
                if p.is_file(): z.write(p,Path(folder.name)/p.relative_to(folder))
        with zipfile.ZipFile(target) as z:
            assert z.testzip() is None
            assert any(n.endswith('src/app/api/data/route.ts') for n in z.namelist())
        print(json.dumps({'file':str(target.resolve()),'bytes':target.stat().st_size,'sha256':digest(target),'zip_crc':'PASS'}))
if __name__=='__main__':main()
