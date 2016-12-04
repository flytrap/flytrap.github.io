# coding: utf8
# auto: flytrap
import os


def get_files(directory, suffix=''):
    # get dir files and filter suffix
    assert os.path.isdir(directory)
    return get_dir_file(directory, suffix)


def get_dir_file(dir_file, suffix=''):
    files = []
    if os.path.isdir(dir_file):
        for f in os.listdir(dir_file):
            files.extend(get_dir_file(os.path.join(dir_file, f), suffix))
    elif os.path.isfile(dir_file) and dir_file.lower().endswith(suffix.lower()):
        files.append(dir_file)
    return files


if __name__ == '__main__':
    index_path = '/home/flytrap/Documents/code/git/flytrap.github.io'
    pp = get_files(index_path, '.html')
    print(len(pp))
