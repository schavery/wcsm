from distutils.core import setup

setup(
	name='WebChangeStopMotion',
	description='Watch file system for changes, to trigger a snapshot of a webpage',
	version='0.1.4',
	author='Steve Avery',
	author_email='schavery@gmail.com',
	scripts=['wcsm'],
	license='LICENSE.txt',
	install_requires=[
		"argparse >= 1.2.1",
		"beautifulsoup4 >= 4.3.2",
		"cssutils >= 1.0",
		"watchdog >= 0.7.1",
		"urllib3 >= 1.7.1"
	]
)

