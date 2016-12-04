# coding: utf8
# auto: flytrap
import os

from common import get_files

Exclude_html = ['index.html', 'template.html']


class SiteMap(object):
    def __init__(self, index_dir, template_html):
        self.index_dir = index_dir
        self.template_html = template_html
        self.check_path()

    def check_path(self):
        assert os.path.isdir(self.index_dir)
        assert os.path.isfile(self.template_html)

    def create_site_map(self):
        files = self.get_html_path()
        self.create_link_block(files)

    def get_html_path(self):
        file_list = get_files(self.index_dir, '.html')
        file_names = map(lambda filename: filename.split(self.index_dir)[1], file_list)
        return filter(lambda filename: filename not in Exclude_html, file_names)

    def create_link_block(self, files):
        d = {}
        d.update(self.get_file_dict(files))
        print(len(d))

    def get_file_dict(self, files, from_=None):
        f_dict = dict()
        for filename in files:
            path_li = filename.split(os.sep)[1:]
            if len(path_li) > 1:
                if path_li[0] not in f_dict:
                    f_dict[path_li[0]] = []
                f_dict[path_li[0]].append(self.get_file_dict(path_li[1:], path_li[0]))
            elif len(path_li) == 0 and from_:
                f_dict[from_] = filename
            else:
                continue
        return f_dict

    def create_links(self, path_li, num):
        if len(path_li) == 1:
            return '<li><a href="#sec-1-1">1.1. install virtualenv</a></li>'


if __name__ == '__main__':
    index_path = '/home/flytrap/Documents/code/git/flytrap.github.io'
    template_html_path = 'template.html'
    sm = SiteMap(index_path, template_html_path)
    sm.create_site_map()
