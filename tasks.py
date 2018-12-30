from invoke import task
import shutil
from pathlib import Path

REGION = 'ap-northeast-1'
S3_BUCKET = 'lambda-function-deploy-packages'
S3_DIR = 'kindle_sale'
DEPLOY_ZIP = 'deploy_package.zip'
DIST_PATH = "dist/packages"


@task
def clean(c, docs=False, bytecode=False, extra=''):
    """
    キャッシュなどを clean する
    :param c:
    :param docs:
    :param bytecode:
    :param extra:
    :return:
    """
    patterns = ['build', 'dist', '*.egg-info']
    if docs:
        patterns.append('docs/_build')
    if bytecode:
        patterns.append('**/*.pyc')
    if extra:
        patterns.append(extra)

    for pattern in patterns:
        # Pathオブジェクトを生成
        current_dir = Path("./")
        path_list = list(current_dir.glob(pattern))

        for path in path_list:
            print("remove : " + str(path))
            shutil.rmtree(str(path))


@task
def build(c, docs=False):
    c.run("python setup.py build")
    if docs:
        c.run("sphinx-build docs docs/_build")


@task
def build_for_lambda(c, no_clean=False):
    """
    aws lambda 用に executable なコードをビルドする
    :param c:
    :param no_clean:
    :return:
    """

    if not no_clean:
        clean(c)

    c.run("mkdir -p {}".format(DIST_PATH))

    file_list = [
        'requirements.txt',
        'constraints.txt',
        'lambda_function.py',
        'lambda_handler/director_of_system.py',
        'lambda_handler/notifier.py',
        'lambda_handler/worker_of_monitor.py',
        'lambda_handler/worker_of_item.py',
    ]
    for file in file_list:
        c.run("cp -p {file} {path}".format(file=file, path=DIST_PATH))

    directory_list = [
        'bin',
        'find_sale_in_wish_list',
    ]
    for directory in directory_list:
        c.run("cp -pR {directory} {path}".format(directory=directory, path=DIST_PATH))

    with c.cd(DIST_PATH):
        c.run('docker run --rm -v "${PWD}":/var/task lambda_headless_chrome')


@task
def upload(c, no_build=False, no_clean=False):
    """
    s3 へコードをアップロードする
    :param c:
    :param no_build:
    :param no_clean:
    :return:
    """

    if not no_build:
        build_for_lambda(c, no_clean)

    with c.cd(DIST_PATH):
        c.run('aws s3 cp {zip} s3://{s3_bucket}/{s3_dir}/'.format(
            zip=DEPLOY_ZIP, s3_bucket=S3_BUCKET, s3_dir=S3_DIR))


@task
def deploy_stack(c, no_build=False, no_clean=False):
    """
    aws cloud formation を使ってコードをデプロイする
    :param c:
    :param no_build:
    :param no_clean:
    :return:
    """

    if not no_build:
        build_for_lambda(c, no_clean=no_clean)

    with c.cd(DIST_PATH):
        c.run('rm -rf deploy_package.zip')

    with c.cd('templates'):
        c.run("aws cloudformation package "
              "--template-file template.yaml "
              "--s3-bucket lambda-function-deploy-packages "
              "--output-template-file packaged.yaml")
        c.run("aws cloudformation deploy "
              "--template-file packaged.yaml "
              "--stack-name find-sale-in-wish-list "
              "--capabilities CAPABILITY_IAM ")


@task
def deploy(c, lambda_name):
    lambda_names = [
        'lambda_headless_chrome_python',
        'worker_scraping_book',
        'worker_scraping_wish_list',
        'worker_user',
    ]

    if lambda_name == 'all':
        for name in lambda_names:
            __deploy_code(c, name)
    else:
        __deploy_code(c, lambda_name)


def __deploy_code(c, name: str)-> None:
    c.run('aws lambda update-function-code '
          + '--region {} '.format(REGION)
          + '--function-name {} '.format(name)
          + '--s3-bucket={} '.format(S3_BUCKET)
          + '--s3-key={s3_dir}/{zip}'.format(s3_dir=S3_DIR, zip=DEPLOY_ZIP))


@task
def create_lambda_function(c, lambda_name):
    c.run('aws lambda create-function '
          + '--region {} '.format(REGION)
          + '--function-name {} '.format(lambda_name)
          + '--runtime python3.6 '
          + '--role arn:aws:iam::267428311438:role/lambda-queue '
          + '--code S3Bucket={s3_bucket},S3Key={s3_dir}/{zip} '.format(s3_bucket=S3_BUCKET, s3_dir=S3_DIR, zip=DEPLOY_ZIP)
          + '--handler lambda_function.{} '.format(lambda_name)
          + '--memory-size 256 --timeout 300 '
          + '--dead-letter-config TargetArn=arn:aws:sns:ap-northeast-1:267428311438:failed-lambda '
          + '--tags service=kindle_sale '
          )


@task
def create_sqs_queue(c, queue_name):
    c.run('aws sqs create-queue '
          + '--region {} '.format(REGION)
          + '--queue-name {} '.format(queue_name)
          + '--attributes VisibilityTimeout=300 '
          )


