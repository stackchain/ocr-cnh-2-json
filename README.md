# ocr-cnh-2-json
OCR for Brazilian CNH (Drivers license) to JSON object.

## Getting started

The simplest and fast-forward way to get started with this project in 2 steps is: 

### Build the docker container

```
docker build -t ocr-cnh .
```

It may take a while as the `Dockerfile` compile and install several OS native libraries to run the service.

### Run the builded container

After waiting for the build, just run an instance of the container by executing:

```
docker run -it -d -p 8080:8080 ocr-cnh
```

You can check if the container is running accordingly by executing the `docker ps`.
Any problems you may have you should take a look at the logs (`docker logs {container_name_or_id}`)

### Ready to go!

At this point you're ready to go. Just access `http://localhost:8080` and you should see a nice and friendly form to test this service :)

# Credits (author)

**Thanks a lot to the original author of this project:** 

 - **[Juliano Lazzarotto](https://github.com/stackchain)** ([his LinkedIn profile](https://www.linkedin.com/in/juliano-lazzarotto/)).

