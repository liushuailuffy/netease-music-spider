# netease-music-spider
网易云音乐爬虫，爬取喜欢的人在一首歌里面有没有评论

<hr>
<h3>使用方法</h3>
修改<a href="https://github.com/liushuailuffy/netease-music-spider/blob/master/Config.py">Config.py</a>中要检测的用户ID，以及获取评论的截止时间，只获取Date日期之后的评论，格式必须为"%Y-%m-%d"
在<a href="https://github.com/liushuailuffy/netease-music-spider/blob/master/music_mysql.py">musci_mysql.py</a>中修改数据库名和密码<strong>mysql数据库</strong>

spider_start.py 启动
