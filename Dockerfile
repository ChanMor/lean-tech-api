# use python 3.11 image
FROM python:3.11


# copy source file to /app
COPY ./api /app/api

WORKDIR /app/api

# install packages
RUN pip install -r /app/api/requirements.txt

# expose port 8000 to be used to received requests
EXPOSE 8000

# run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
