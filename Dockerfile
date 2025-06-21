FROM python:3.11

ENV DEPLOY=1

WORKDIR /opt/tmp

COPY . /opt/tmp/

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

EXPOSE 80

CMD ["sh","start.sh"]

