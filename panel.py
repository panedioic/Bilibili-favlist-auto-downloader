#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
import aiohttp
import asyncio
import time
import json
import os
import re

from config import config as user_config

routes = web.RouteTableDef()



@routes.get('/')
async def index(request):
    await asyncio.sleep(0.1)
    return web.Response(body=b'<h1>Index</h1>', headers={'content-type': 'text/html'})
    
    
@routes.get('/panel')
async def panel(request):
    with open(user_config['down_folder']+'index.html',  encoding='utf-8') as file_obj:
        panel_html = file_obj.read()
        return web.Response(body=panel_html, headers={'content-type': 'text/html'})

@routes.get('/jsondata')
async def get_data(request):
    with open(user_config['down_folder'] + 'vid_info.json', 'r') as f:
        data = json.load(f)
        return web.json_response(data,status=200)

@routes.get('/danmaku/v3/')
async def get_danmaku(request):
    dm_dir = user_config['down_folder']+'danmakus'
    cid = request.query.get('id', '0')

    max = [0,0,0,0]
    destcid = cid

    for dmfile in os.listdir(dm_dir):
        fl = dmfile.split('-')
        if(len(fl) < 4):
            continue
        if(fl[1] == destcid and int(fl[2]) > int(max[2])):
            max = fl

    print(max)
    dm_path = dm_dir+'/'+max[0]+'-'+max[1]+'-'+max[2]+'-'+max[3]

    dm_xml = ''
    with open(dm_path,  encoding='utf-8') as dmfile:
        dm_xml = dmfile.read()

    #<d p=”弹幕出现时间,模式,字体大小,颜色,发送时间戳,弹幕池,用户Hash,数据库ID”>123123</d>
    #[item.time || 0, item.type || 0, item.color || 16777215, htmlEncode(item.author) || 'DPlayer', htmlEncode(item.text) || ''])
    pat_dm = re.compile(r'<d p="([0-9\.]+),([0-9]+),([0-9]+),([0-9]+),([0-9]+),([0-9]+),([0-9a-fA-F]+),([0-9]+)">(.*?)</d>')

    dm_list = pat_dm.findall(dm_xml)

    dm_data = []

    for dm in dm_list:
        tmp_list=[]
        tmp_list.append(float(dm[0]))
        if(dm[1]=='0'):
            tmp_list.append(0)
        else:
            tmp_list.append(-int(dm[1])+6)
        tmp_list.append(dm[3])
        tmp_list.append(dm[6])
        tmp_list.append(dm[8])
        dm_data.append(tmp_list)

    return web.json_response({'code':0,'data':dm_data},status=200)


@routes.get('/hello/{name}')
async def hello2(request):
    await asyncio.sleep(0.1)
    return web.Response(body="<h1>hello %s</h1>" % request.match_info['name'], headers={'content-type': 'text/html'})

app = web.Application()
app.add_routes(routes)
app.router.add_static('/css/',
                      path=user_config['down_folder']+'css',
                      name='css')
app.router.add_static('/js/',
                      path=user_config['down_folder']+'js',
                      name='js')
app.router.add_static('/image/',
                      path=user_config['down_folder']+'image',
                      name='image')
app.router.add_static('/covers/',
                      path=user_config['down_folder']+'covers',
                      name='covers')
app.router.add_static('/template/',
                      path=user_config['down_folder']+'template',
                      name='template')
app.router.add_static('/video/',
                      path=user_config['down_folder']+'video',
                      name='video')

#loop=asyncio.get_event_loop()
#loop.create_task(ctx_handeler())
#loop.run_until_complete(web.run_app(app))

web.run_app(app, port=user_config['webpanel_port'])