from setuptools import setup

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
                'mannequin/TPS'])
