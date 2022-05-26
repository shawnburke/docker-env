from setuptools import setup
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


setup(
   name='docker_env_client',
   version='0.1',
   description='Client for docker-env dev server system',
   author='Shawn Burke',
   author_email='shawn@shawnburke.com',
   license="MIT",
   packages=['docker_env_client'], 
   install_requires=['httpx', 'attrs', 'mock'],
)
