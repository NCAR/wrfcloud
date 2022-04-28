from setuptools import setup

setup(
    name='wrfcloud',
    version='0.0.0',
    description='NCAR/RAL WRF Cloud Framework',
    author='David Hahn',
    author_email='hahnd@ucar.edu',
    maintainer='David Hahn',
    maintainer_email='hahnd@ucar.edu',
    packages=['wrfcloud', 'wrfcloud/dynamodb', 'wrfcloud/imagebuilder'],
    install_requires=['boto3', 'pyyaml', 'argparse'],
    package_dir={'wrfcloud': 'wrfcloud'},
    package_data={
        'wrfcloud': [
          'imagebuilder/imagebuilder.yaml'
        ]
    },
    include_package_data=True,
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'wrfimagebuilder=wrfcloud.imagebuilder:main'
        ]
    }
)
