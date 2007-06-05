from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='CmdUtils',
      version=version,
      description="Routines to help make command-line utilities easier to write",
      long_description="""\
""",
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
      ],
      keywords='command line option parsing optparse',
      author='Ian Bicking',
      author_email='ianb@colorstudy.com',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [paste.paster_create_template]
      cmdutils = cmdutils.templates:CmdTemplate
      """,
      )
