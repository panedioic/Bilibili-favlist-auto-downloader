# Bilibili-favlist-auto-downloader
Bilibili favlist auto downloader 是一个开源的 Bilibili 辅助工具，主要用途为自动检测设定的B站的收藏夹内的视频，定期自动下载并更新弹幕，以便于在你收藏的视频被删除后仍然可以观看。
项目自带的前端页面可以方便地看到已下载的视频并可以在前端直接观看，不需要准备支持弹幕功能的播放器。
项目需要 aria2 支持以达到最佳使用体验，如果你不想安装 aria2, 你仍可以通过简单地修改代码继续使用，只不过下载速度可能会减慢。

## 如何使用？
### 准备要下载的收藏夹id
收藏夹的id可以在收藏的页面通过f12开发者工具找到。
打开f12之后打开任意一个收藏夹，在 Network 中找到形如 https://api.bilibili.com/x/v3/fav/resource/list?media_id=111111&pn=1&ps=20&keyword=&order=mtime&type=0&tid=0&jsonp=jsonp 的链接， media_id 即为要找的收藏夹id。

### Cookie
为了下载最高的清晰度，使用时需准备自己的 cookie。你只需要在刚才的链接的 request headers 中找到 cookie 并复制到 config.py 的 cookie 项即可。

## 关于
因为我不太会写前端，所以本项目的前端页面大多借鉴了Meloduet-Bilibili-Video-Fetcher 的项目。

本项目还存在着一些 bugs, 但我不一定会修,,,如果你能帮我解决那我会非常感谢。