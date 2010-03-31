from setuptools import setup, find_packages

version = '0.1'

setup(name='CmdUtils',
      version=version,
      description="Routines to help make command-line utilities easier to write",
      long_description="""\
Some utilities for writing command-line utilities.

This primarily implements a logging system for script output.
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
      url='http://pythonpaste.org/cmdutils/',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      entry_points="""
      [paste.paster_create_template]
      cmdutils = cmdutils.templates:CmdTemplate
      """,
      )
