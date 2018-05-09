FROM library/python
RUN apt-get update && apt-get install curl
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py
RUN pip install docker-compose
CMD ["python", "/floop/hello.py"]
