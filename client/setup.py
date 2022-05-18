from setuptools import setup

setup(
   name='docker-env-client',
   version='0.1',
   description='Client for docker-env dev server system',
   author='Shawn Burke',
   author_email='shawn@shawnbure.com',
   packages=['httpx', 'attrs'],  # would be the same as name
   install_requires=[], #external packages acting as dependencies
)
