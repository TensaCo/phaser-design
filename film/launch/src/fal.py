import sys, json, time, urllib.request
key=[l.split('=',1)[1].strip().strip('"') for l in open('/home/brandonin/Documents/commandagi/.env') if l.startswith('FAL_KEY=')][0]
H={'Authorization':'Key '+key,'Content-Type':'application/json'}
import subprocess
def req(url, data=None):
    cmd=['curl','-s','-m','120','-H','Authorization: '+H['Authorization'],'-H','Content-Type: application/json',url]
    if data is not None: cmd[1:1]=['-X','POST','-d',json.dumps(data)]
    return json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
def run(endpoint, payload, out):
    sub=req('https://queue.fal.run/'+endpoint, payload)
    print('submitted', sub.get('request_id'), flush=True)
    st_url, res_url = sub['status_url'], sub['response_url']
    t0=time.time()
    while True:
        st=req(st_url)
        if st.get('status')=='COMPLETED': break
        if time.time()-t0>1500: print('timeout', st); return
        time.sleep(5)
    r=req(res_url)
    urls=[i['url'] for i in r.get('images',[])] or ([r['video']['url']] if 'video' in r else [])
    if not urls: print('no output', json.dumps(r)[:500])
    for n,u in enumerate(urls):
        if u.startswith('data:'):
            import base64
            head,b=u.split(',',1); ext=head.split('/')[1].split(';')[0]
            p=f'{out}-{n}.{ext}'; open(p,'wb').write(base64.b64decode(b))
        else:
            ext=u.split('?')[0].rsplit('.',1)[-1]
            p=f'{out}-{n}.{ext}'; subprocess.run(['curl','-s','-m','300','-o',p,u])
        u=u[:80]; print('saved', p, u, flush=True)
if __name__=='__main__':
    run(sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3])
