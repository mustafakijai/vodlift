from playwright.sync_api import sync_playwright
import sys, pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
url=(ROOT/'index.html').as_uri()
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for name,vp,scale,mob in [('desktop',{'width':1440,'height':900},1,False),('mobile',{'width':390,'height':844},2,True)]:
        pg=b.new_page(viewport=vp,device_scale_factor=scale,is_mobile=mob,has_touch=mob,reduced_motion='reduce')
        errs=[]; pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
        pg.goto(url); pg.wait_for_load_state('networkidle')
        pg.evaluate("document.querySelectorAll('.rv').forEach(e=>e.classList.add('in'))")
        pg.wait_for_timeout(600)
        sw=pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        print(name,'scrollWidth/innerWidth',sw,'errors',errs)
        pg.screenshot(path=str(ROOT/f'preview-{name}.png'),full_page=True)
    b.close()
