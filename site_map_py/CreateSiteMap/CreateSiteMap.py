# coding: utf8
# auto: flytrap
import os
import re

from common import get_files

title_re1 = re.compile('<h1\s+class="title">(.*?)</h1>')
title_re2 = re.compile('{{ title }}')
links_re = re.compile('{{ blog_links }}')
Exclude_html = ['index.html', 'template.html']


class SiteMap(object):
    def __init__(self, index_dir, template_html):
        self.index_dir = index_dir
        self.template_html = template_html
        self.site_map_path = os.path.join(self.index_dir, 'site_map.html')
        self.title = 'Flytrap Site Map'
        self.check_path()

    def check_path(self):
        assert os.path.isdir(self.index_dir)
        assert os.path.isfile(self.template_html)

    def create_site_map(self):
        files = self.get_html_path()
        links_html = self.create_link_block(files)
        with open(self.template_html) as f:
            html_text = f.read()
            site_map_html = links_re.sub(links_html, html_text)
            site_map_html = title_re2.sub(self.title, site_map_html)
            with open(self.site_map_path, 'w') as site_map_file:
                site_map_file.write(site_map_html)
                print('site create ok...')

    def get_html_path(self):
        file_list = get_files(self.index_dir, '.html')
        file_names = map(lambda filename: filename.split(self.index_dir)[1], file_list)
        return filter(lambda filename: filename.split('/')[-1] not in Exclude_html, file_names)

    def create_link_block(self, files):
        path_dict = self.path_links_dict(files)
        html_text = self.create_html(path_dict)
        return html_text

    def create_html(self, path_dict):
        html_text = ''
        if isinstance(path_dict, dict):
            for cat, blog_list in path_dict.iteritems():
                html_text += '<ul>'
                html_text += '<li>%s' % cat
                html_text += self.create_html(blog_list)
                html_text += '</li></ul>'
        elif isinstance(path_dict, list):
            html_text += '<ul>'
            for blog in path_dict:
                if isinstance(blog, basestring):
                    html_text += self.create_html_links(blog)
                else:
                    html_text += self.create_html(blog)  # dict
            html_text += '</ul>'
        return html_text

    def path_links_dict(self, files):
        path_dict = {}
        for filename in files:
            html_path = filename.split('/')
            f_len = len(html_path) - 1
            if f_len == 1:
                if '/' not in path_dict:
                    path_dict['/'] = []
                path_dict['/'].append(filename)
                continue
            if html_path[1] not in path_dict:
                path_dict[html_path[1]] = []
            if f_len == 2:
                path_dict[html_path[1]].append(filename)
                continue
            for i in xrange(f_len):
                path_dict[html_path[1]].append((self._links_dict(html_path[2:], filename)))
                break
        return path_dict

    def _links_dict(self, html_path, filename):
        path_dict = {}
        if len(html_path) <= 2:
            path_dict[html_path[0]] = [filename]
        else:
            path_dict[html_path[0]] = self._links_dict(html_path[1:], filename)
        return path_dict

    def create_html_links(self, path_li):
        file_path = self.index_dir + path_li
        title = ''
        if os.path.isfile(file_path):
            with open(file_path) as f:
                html = f.read()
                html_title = title_re1.findall(html)
                if html_title:
                    title = html_title[0]
        if not title:
            title = path_li.split('/')[-1].split('.html')[0]
        return '<li><a href="%s">%s</a></li>\n' % (path_li, title)


if __name__ == '__main__':
    index_path = '/home/flytrap/Documents/code/git/flytrap.github.io'
    template_html_path = 'template.html'
    sm = SiteMap(index_path, template_html_path)
    sm.create_site_map()
