import asyncio
import nest_asyncio
import json
from pyppeteer import launch
import time
import re

request_data = []
def CalcCountWaitReq():
  global request_data
  count_wait=0;
  for req_data in request_data:
    if req_data['type']=='no_load'  and  'google' not in req_data['url'] and  'yandex' not in req_data['url'] and 'gstatic.com' not in req_data['url']:
      count_wait=count_wait+1;
     # print(req_data['url'])
  return count_wait
async def waitForNetworkIdle(page, idle_time=1000, timeout=58000):
    global request_data
    counts=0
    while True:
      
      if(CalcCountWaitReq()==0):
        await asyncio.sleep(idle_time / 1000)
        if(CalcCountWaitReq()==0):
          break
     # print(count_wait)
      await asyncio.sleep(idle_time / 1000)
      timeout -= idle_time
      if timeout <= 0:
        break
      counts=counts+1;
def ChecUnicReq(url):
  global request_data
  for req_data in request_data:
      if req_data['url'] == url:
        return False
  return True

async def clickElement(page,selector):
  pat = re.compile(r'\[innerText\*?=([^\]]+)\]')
  textSel = pat.search(selector)
  if textSel:
    text_filter = textSel.group()
    selector = selector[:textSel.start()] + selector[textSel.end():]
    cod_func="""() => {let sel='"""+selector+"""';
    let text_filt='"""+text_filter+"""'
    async function WaitSFn(sel,text_filt){
        for(let i=0;i<5;i++){
            let find_fn=text_filt.indexOf('*=')!=-1?'index':'equal';
            let filt=text_filt.split('=')[1].replace(']','').toLowerCase();
            let list=Array.from(document.querySelectorAll(sel)).filter(el=>{   
                let texts=el.innerText.trim().toLowerCase();
                if(find_fn=='index')
                    return texts.indexOf(filt)!=-1
                else
                    return texts==filt
            })
            if(list.length>0){
                list[0].click();
                break;
            }else{
                await new Promise(sup=>{setTimeout(sup,1000)})
                console.log('wait')
            }
        }
    }
    return WaitSFn(sel,text_filt)
    }"""
    await page.evaluate(cod_func) 
  else:
    link = await page.querySelector(selector)
    await link.click()
#clickElement(0,'sad[innerText=sdf]')

async def ScripPage(page,commands):#,
  for command in commands:
    command_type = type(command)
    if command_type==str:
        if(command=='file'):
          await waitForNetworkIdle(page)
        else:
          func = globals()[command]
          await func();
        print('str_fn'+command)
    elif command_type==int:
        await asyncio.sleep(command)
        print('str_sleep'+str(command))
    elif command_type==dict:
        key, value = next(iter(command.items()))
        if key=='click':
          await clickElement(page,value)
        else:
          print('str_page'+key)
          fn=getattr(page, key)
          if isinstance(value, list):
              await fn(*value)            
          else:
              await fn(value) 
        
    
def CheckBlockRequest(pattern,url):
  if(type(pattern)==str):
    return pattern not in url;
  else:
    for pat in pattern:
      if pat in url:
        return False
    return True

async def greet(param):
    prog_param=json.loads(param)
    
    print('start')
    browser = await launch({'headless': True,'args':['--no-sandbox','--use-gl=angle','--disable-setuid-sandbox']})
    
    print('page')
    page = await browser.newPage()
    print('page_load')
    await page.setRequestInterception(True)
    page.on('request', lambda request: 
            asyncio.create_task(request.continue_()) 
            if CheckBlockRequest(prog_param['pattern'],request.url)  else asyncio.create_task(
    request.abort()))

    page.on('request', lambda request: 
        (request_data.append({
            'url': request.url,
            'type': 'no_load',
            'size': 0
        })) if request.url.startswith("http") and ChecUnicReq(request.url) else None
    )
    async def response_handler(response,types):
        
          for req_data in request_data:
            try:
              if req_data['url'] == response.url:
                  if types=='good':
                    req_data['type'] = 'response'
                    req_data['size'] = -1
                    if response.status==200:
                      response_body = await response.buffer()
                      size_val=len(response_body)
                      req_data['size'] = size_val
                    
                    req_data['total_time'] =time.time() - page_start_time

                    
                  else:
                    req_data['type'] = 'error'
                  break
            except Exception as e:
              req_data['type'] = 'error'


    page.on('response', lambda response: asyncio.create_task(response_handler(response,'good')))
    page.on('requestfailed', lambda response: asyncio.create_task(response_handler(response,'bad')))
    print('req')
    # Log all requests made by the page
    
    
   
    # Load the webpage
    page_start_time = time.time()
    if('defTimeput' in prog_param):
      page.setDefaultNavigationTimeout(prog_param['defTimeput'])
    await page.goto(prog_param['url'],{"referer":prog_param['url']})
    if('viewport' in prog_param):
       await page.setViewport({'width': prog_param['viewport'][0], 'height': prog_param['viewport'][1]})

    print('loads')

    #await asyncio.sleep(1)
    #await waitForNetworkIdle(page);
    #await asyncio.sleep(5)
    #await waitForNetworkIdle(page)
    await asyncio.sleep(10)
    await waitForNetworkIdle(page)
    await asyncio.sleep(3)
    await waitForNetworkIdle(page)
    if('script' in prog_param):
      await ScripPage(page,prog_param['script'])

    res={};
    print(request_data);
    res['timeLoad']=time.time() - page_start_time;
    res['amountRequests']=len(request_data)
    doc_size=-1;
    full_size=0;
    itog_file_list=[];
    for req_data in request_data:
        if 'size' in req_data:
            full_size += req_data.get('size', 0)
            if doc_size==-1 and req_data['size']!=-1:
                doc_size=req_data['size']
        
    
    res['documentSize']=doc_size
    res['fullSize']=full_size
    res['fileList']=request_data
    if('screen_quality' in prog_param):
        quality=prog_param['screen_quality']
    else:
        quality=70;
    await page.screenshot({'fullPage': True,"path": 'google.png','type':'jpeg','quality':quality})    
    res['screenShotData']=await page.screenshot({'fullPage': True,'encoding':'base64','type':'jpeg','quality':quality})
    await browser.close()
    print(res)
    return "Hello "

def get_screenshot_gradio(url):
    nest_asyncio.apply()
    print(asyncio.get_event_loop().run_until_complete(greet(url)))
    return '1'
    

#param='{"url":"https://www.megaigry.ru/embed/bank-robbery/","pattern":"jquery.min.js","screen_quality":70,"defTimeput":29999,"script":["file",10,{"click":"button[innerText=Играть]"}]}'#,{"click":".play-button"},"file",5
param='{"url":"https://html5.gamemonetize.co/8ezvpp4wfi3zclyb5ms9ncbxvkjy7i2g/","pattern":"456465456","screen_quality":70,"defTimeput":29999,"script":["file",10,{"click":"#promo-button[innerText=SKIP]"},"file",10]}'



get_screenshot_gradio(param)
