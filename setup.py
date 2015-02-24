try:
    from setuptools import setup
except:
    from distutils.core import setup

config = {
    'description': 'Run scripts with a websocketey wrapper to pipe out the output.',
    'author': 'Luke Hospadaruk',
    'url': 'https://github.com/hospadar/socket-executor',
    'download_url': 'https://github.com/hospadar/socket-executor.git',
    'author_email': 'luke@hospadaruk.org',
    'version': '0.1',
    'install_requires': ['tornado'],
    'packages': ['socket_executor'],
    'scripts': ['socket-server.py'],
    'package_data': {'socket-server':'static/*'},
    'name': 'socket_executor'
}

setup(**config)