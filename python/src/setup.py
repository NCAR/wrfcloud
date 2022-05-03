from setuptools import setup

setup(
    name='wrfcloud',
    version='0.0.1',
    description='NCAR/RAL WRF Cloud Framework',
    author='David Hahn',
    author_email='hahnd@ucar.edu',
    maintainer='David Hahn',
    maintainer_email='hahnd@ucar.edu',
    packages=['wrfcloud', 'wrfcloud/dynamodb', 'wrfcloud/imagebuilder'],
    install_requires=['boto3', 'pyyaml', 'argparse', 'bcrypt', 'PyJWT'],
    package_dir={'wrfcloud': 'wrfcloud'},
    package_data={
        'wrfcloud': [
            'resources/env_vars.yaml',
            'resources/logo.jpg',
            'resources/password_reset.html',
            'resources/welcome_email.html',
            'imagebuilder/imagebuilder.yaml',
            'user/table.yaml'
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
