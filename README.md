Find kindle books in wish list on AWS lambda 
==================================================

Table of Contents
-----------------

* [Description](#description)
* [Requirements](#requirements)
* [Usage](#usage)

Description
-----------

* ウィッシュリストに登録してされているkindle本が以下の条件を満たした時にslackに通帳します
    - ポイント還元率が一定値以上に達する
    - 割引き率が一定値以上に達する
* AWS lambda 上で動作します


Requirements
------------

* 公開された amazon wish list 
* docker
* python 3.6.3

Usage
-----


1. docker イメージの build
    - `docker build -t lambda_headless_chrome .`
1. aws lambda へのアップロード
    - `sh ./upload.sh`
1. CloudWatch Event で lambda を定期実行するようにする 

* 必要な環境変数
    - `slackPostURL`
    - `slackChannel`