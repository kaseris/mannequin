import os
import os.path as osp
from setuptools import setup


def data_package_files(directory):
    paths = []
    for path, directories, filenames in os.walk(directory):
        for filename in filenames:
            paths.append(('mannequin/'+path, [osp.join(path, filename)]))
    return paths


extra_files = data_package_files('data')

setup(name='mannequin',
      version='0.1',
      description='Test',
      author='kaseris',
      author_email='kaseris@iti.gr',
      license='MIT',
      packages=['mannequin',
                'mannequin/fileio',
                'mannequin/primitives',
                'mannequin/lerp',
                'mannequin/detection',
                'mannequin/retrieval3d',
                'mannequin/TPS'],
      package_data={'': ['conf.json']},
      data_files=extra_files,
      include_package_data=True
      )
