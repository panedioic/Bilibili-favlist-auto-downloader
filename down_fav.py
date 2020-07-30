import requests
import os
import time
import json
import sqlite3

from config import config as user_config

res_dict = {
    'fav_list': 'https://api.bilibili.com/x/v3/fav/resource/list?media_id={id}&pn={pn}&ps=20&keyword=&order=mtime&type=0&tid=0&jsonp=jsonp',
    'page_list': 'https://www.bilibili.com/widget/getPageList?aid={aid}',
    'qn': 'https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&otype=json',
    'play_url': 'https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&otype=json&qn={qn}',
    'dm_url': 'https://api.bilibili.com/x/v1/dm/list.so?oid={cid}',
    'origin': 'https://bilibili.com/video/{bvid}',
    
    'headers': {
        "referer": "https://www.bilibili.com/video/BV1ox411S7Q7",
        "cookie": user_config['cookie'],
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36"
        }
}


video_list = []
cid_list=[] # Save downloaded cid

def check_video(cid):
    conn = sqlite3.connect(user_config['down_folder']+'vidinfo.db')
    cursor = conn.cursor()

    cursor.execute('select * from vid_table where id=?', (cid,))
    values = cursor.fetchall()

    cursor.close()
    conn.close()

    return values

def addinfo_video(data):
    conn = sqlite3.connect(user_config['down_folder']+'vidinfo.db')
    cursor = conn.cursor()

    try:
        cursor.execute('insert into vid_table (id, aid, title, pagename, cover, upper, upperid, intro, pubtime, length) values (?,?,?,?,?,?,?,?,?,?)', data)
    except sqlite3.IntegrityError as e:
        pass

    cursor.close()
    conn.commit()
    conn.close()


def get_favList(fid):
    tmp_list = []
    req = requests.get(res_dict['fav_list'].format(id=fid,pn=1))
    jsondata = req.json()

    fav_pages = (int(jsondata['data']['info']['media_count']) - 1) // 20 + 1

    for page in range(1,fav_pages+1):
        req = requests.get(res_dict['fav_list'].format(id=user_config['fav_id'],pn=page))
        tmp_list += req.json()['data']['medias']

    return tmp_list


def down_video_local(aid, cid):
    # get max qn 
    req_getqn = requests.get(res_dict['pn'].format(aid=aid, cid=cid))
    qn = req_getqn.json()['data']['accept_quality'][0]

    get_videourl = requests.get(res_dict['play_url'].format(aid=aid, cid=cid, qn=qn)).json()['data']['durl'][0]['url']

    get_video = requests.get(get_videourl, headers=res_dict['headers'], stream=True)

    f=open('./back_video/{aid}-{cid}.mp4'.format(aid=aid, cid=cid),'wb')
    for chunk in get_video.iter_content(chunk_size=32):#iter是iter
        f.write(chunk)

def get_down_url(aid, cid):
    # get max qn
    req_getqn = requests.get(res_dict['qn'].format(aid=aid, cid=cid))
    qn = req_getqn.json()['data']['accept_quality'][0]
    #print(res_dict['play_url'].format(aid=aid, cid=cid, qn=qn))

    get_videourl = requests.get(res_dict['play_url'].format(aid=aid, cid=cid, qn=qn), headers=res_dict['headers']).json()['data']['durl'][0]
    #print(get_videourl)
    return (get_videourl['url'], get_videourl['length'], get_videourl['size'])

def down_video_aria2(aid, bid, cid):
    (down_url, video_length, video_size) = get_down_url(aid, cid)

    jsondata={
        "jsonrpc":"2.0",
        "id":bid+str(cid),
        }

    reqdata = jsondata
    reqdata["method"] = "aria2.tellActive"  
    ret = requests.post(user_config['ariaurl'], json=reqdata)
    #print(ret.json())
    curdowns=len(ret.json()["result"])
    while curdowns >= user_config['max_downs']:
        #print("[info]Waitting for links...")
        time.sleep(2)                  #等不到就睡一觉
        ret = requests.post(user_config['ariaurl'], json=reqdata)
        curdowns=len(ret.json()["result"])
    reqdata["method"] = "aria2.addUri"            #aria  增加下载的方法
    reqdata['params'] = [[],{}]
    reqdata['params'][0] = [down_url]
    reqdata['params'][1] = {"out" : str(aid)+'-'+str(cid)+'.flv',"dir" : user_config['down_folder']+'video/', "referer": res_dict['origin'].format(bvid=bid),"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0"}
    ret = requests.post(user_config['ariaurl'], json=reqdata)
    return video_length

def down_video(aid, bid, cid):
    if user_config['down_type'] == 'aria2':
        down_video_aria2(aid, bid, cid)

def down_danmaku(aid, cid):
    get_danmaku = requests.get(res_dict['dm_url'].format(cid=cid), headers=res_dict['headers'], stream=True)

    f=open(user_config['down_folder']+'danmakus/{aid}-{cid}-'.format(aid=aid, cid=cid)+'%s.xml'%time.strftime("%Y%m%d-%H%M", time.localtime()),'wb')
    for chunk in get_danmaku.iter_content(chunk_size=32):#iter是iter
        f.write(chunk)

def down_cover(url, aid, cid):
    get_cover = requests.get(url, headers=res_dict['headers'], stream=True)

    f=open(user_config['down_folder']+'covers/{aid}-{cid}.png'.format(aid=aid, cid=cid),'wb')
    for chunk in get_cover.iter_content(chunk_size=32):#iter是iter
        f.write(chunk)

def data_jsonify():
    conn = sqlite3.connect(user_config['down_folder']+'vidinfo.db')
    cursor = conn.cursor()
    cursor.execute('select * from vid_table')
    values = cursor.fetchall()

    #print(values)

    vid_data=[]

    ## id, aid, title, pagename, cover, upper, upperid, intro, pubtime, length

    for video in values:
        vid_data.append({
            "id": video[0],
            "aid": video[1],
            "title": video[2],
            "pagename": video[3],
            "cover": video[4],
            "upper": video[5],
            "upperid": video[6],
            "intro": video[7],
            "pubtime": video[8],
            "length": video[9]
        })

    data = {
        "data": vid_data
    }

    with open(user_config['down_folder']+'vid_info.json', 'w') as f:
        json.dump(data, f)


    cursor.close()
    conn.close()

# main

if not os.path.exists(user_config['down_folder']):
    os.makedirs(user_config['down_folder'])

video_list = get_favList(user_config['fav_id'])

conn = sqlite3.connect(user_config['down_folder']+'vidinfo.db')
cursor = conn.cursor()
try:
    cursor.execute('create table vid_table (id integer(20) primary key, aid integer, title varchar(255), pagename text, cover text, upper text, upperid integer, intro text, pubtime integer, length integer)')
except sqlite3.OperationalError as e:
    pass
cursor.close()
conn.commit()
conn.close()

# init end

while True:

    for video in video_list:
        if(video['title']=='已失效视频'):
            continue

        bvid = video['bvid']
        #cover = video['cover']
        #intro = video['intro']
        #video['pubtime']
        #video['upper']['name']

        #cid-data-durl-0-length/size

        cids = requests.get(res_dict['page_list'].format(aid=video['id'])).json()

        for cid in cids:
            print('[info]aid-{aid}/cid-{cid} checked.'.format(aid=video['id'], cid=cid['cid']))
            if len(check_video(cid['cid'])) == 0:
                video_length = down_video(video['id'], bvid, cid['cid'])
                down_cover(video['cover'], video['id'], cid['cid'])

                # id, aid, title, pagename, cover, upper, upperid, intro, pubtime, length
                data = (cid['cid'], video['id'], video['title'], cid['pagename'], video['cover'], video['upper']['name'], video['upper']['mid'], video['intro'], video['pubtime'], video_length)
                #cid_list.append(cid['cid'])
                addinfo_video(data)
                print('[info]aid-{aid}/cid-{cid} downloaded.'.format(aid=video['id'], cid=cid['cid']))
            down_danmaku(video['id'], cid['cid'])

    data_jsonify()

    print(time.strftime("[info][%Y%m%d-%H:%M:%S]", time.localtime()), end=' ')
    print('Video check ended, waiting for next check...')

    time.sleep(3600 * 4)