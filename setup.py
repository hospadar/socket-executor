from setuptools import setup

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
    'name': 'socket_executor',
    'include_package_data':True
}

setup(**config)