from distutils.core import setup

setup(
	name='WebChangeStopMotion',
	description='Watch file system for changes, to trigger a snapshot of a webpage',
	version='0.1.5',
	author='Steve Avery',
	author_email='schavery@gmail.com',
	scripts=['wcsm'],
	license='LICENSE.txt',
	install_requires=[
		"argparse >= 1.2.1",
		"beautifulsoup4 >= 4.3.2",
		"chardet >= 2.0.1",
		"cssutils >= 1.0",
		"requests >= 2.2.1",
		"watchdog >= 0.7.1"
	]
)

