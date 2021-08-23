import codecs

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='flexmock',
      version='0.10.7',
      author='Slavek Kabrda, Herman Sheremetyev',
      author_email='slavek@redhat.com',
      url='http://flexmock.readthedocs.org',
      license='BSD License',
      py_modules=['flexmock'],
      description='flexmock is a testing library for Python that makes it easy to create mocks,'
                  'stubs and fakes.',
      long_description=codecs.open('README.rst', encoding='utf8').read(),
      keywords='flexmock mock stub test unittest pytest nose',
      classifiers=[
          'License :: OSI Approved :: BSD License',
          'Intended Audience :: Developers',
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: Implementation :: Jython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Topic :: Software Development :: Testing',
      ],
      )
