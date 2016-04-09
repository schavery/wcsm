from distutils.core import setup

setup(
	name='WebChangeStopMotion',
	description='Watch file system for changes, to trigger a snapshot of a webpage',
	version='0.2.0',
	author='Steve Avery',
	author_email='schavery@gmail.com',
	scripts=['wcsm'],
	license='LICENSE.txt',
	install_requires=[
		"argparse >= 1.4.0",
		"beautifulsoup4 >= 4.4.1",
		"chardet >= 2.3.0",
		"cssutils >= 1.0.1",
		"requests >= 2.9.1",
		"watchdog >= 0.8.3",
		"lxml >= 3.6.0"
	]
)

