# flytrap.github.io

hexo-flytrap blog

安装博客
首先要安装node
``` bash
git clone http://github.com/flytrap/flytrap.github.io.git

git fetch origin hexo-flytrap  # 安装分支
git checkout hexo-flytrap  # 切换分支
cnpm install  # 安装依赖的包

git clone https://github.com/litten/hexo-theme-yilia.git themes/yilia

cp yilia_config.yml themes/yilia/_config.yml

hexo clean
hexo g
hexo server
hexo deploy
