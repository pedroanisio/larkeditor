from setuptools import setup, find_packages

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='larkeditor-web',
    version='2.0.0',
    packages=find_packages(),
    include_package_data=True,

    url='https://github.com/poletaevvlad/larkeditor',
    license='BSD 2-Clause License',
    author='Vlad Poletaev',
    author_email='poletaev.vladislav@gmail.com',
    description='Web-based EBNF grammar editor for Lark parsing library',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
    ],

    entry_points={
        "console_scripts": [
            "larkeditor-web = app.main:main",
            "larkeditor-dev = run_dev:main"
        ]
    },

    install_requires=requirements,
    python_requires='>=3.8',
    
    # Package data
    package_data={
        'app': [
            'templates/*.html',
            'static/**/*',
        ],
    },
    
    # Additional metadata
    project_urls={
        'Documentation': 'https://github.com/poletaevvlad/larkeditor',
        'Source': 'https://github.com/poletaevvlad/larkeditor',
        'Tracker': 'https://github.com/poletaevvlad/larkeditor/issues',
    },
)
