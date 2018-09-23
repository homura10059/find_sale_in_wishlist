from invoke import task


region = 'ap-northeast-1'
s3_bucket = 'lambda-function-deploy-packages'
s3_dir = 'kindle_sale'
deploy_zip = 'deploy_package.zip'


@task
def clean(c, docs=False, bytecode=False, extra=''):
    patterns = ['build', 'deploy']
    if docs:
        patterns.append('docs/_build')
    if bytecode:
        patterns.append('**/*.pyc')
    if extra:
        patterns.append(extra)
    for pattern in patterns:
        c.run("rm -rf {}".format(pattern))


@task
def build(c, docs=False):
    c.run("python setup.py build")
    if docs:
        c.run("sphinx-build docs docs/_build")


@task
def upload(c):
    clean(c)

    c.run("mkdir deploy")

    file_list = [
        'requirements.txt',
        'lambda_function.py',
    ]
    for file in file_list:
        c.run("cp -p {file} deploy/".format(file=file))

    directory_list = [
        'bin',
        'memorize',
        'scraping',
    ]
    for directory in directory_list:
        c.run("cp -pR {directory} deploy/".format(directory=directory))

    with c.cd('deploy'):
        c.run('docker run --rm -v "${PWD}":/var/task lambda_headless_chrome')
        c.run('aws s3 cp {zip} s3://{s3_bucket}/{s3_dir}/'.format(
            zip=deploy_zip, s3_bucket=s3_bucket, s3_dir=s3_dir))


@task
def deploy(c, lambda_name='all'):
    lambda_names = [
        'lambda_headless_chrome_python',
        'worker_scraping_book',
        'worker_scraping_wish_list',
    ]

    if lambda_name == 'all':
        for name in lambda_names:
            __deploy_code(c, name)
    else:
        __deploy_code(c, lambda_name)


def __deploy_code(c, name: str)-> None:
    c.run('aws lambda update-function-code '
          + '--region {} '.format(region)
          + '--function-name {} '.format(name)
          + '--s3-bucket={} '.format(s3_bucket)
          + '--s3-key={s3_dir}/{zip}'.format(s3_dir=s3_dir, zip=deploy_zip))
