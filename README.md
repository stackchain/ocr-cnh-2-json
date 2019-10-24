# ocr-cnh-2-json
OCR for Brazilian CNH (driver's license) to JSON object. It will try to read all the driver's license data, and allows you to compare match the similarity of a selfie against the document photo.

## Getting started

The simplest way to get started with this project in 2 steps:

### Build the docker container

```
docker build -t ocr-cnh .
```

It may take a while as the `Dockerfile` compiles and install several OS native libraries to run the service.

### Run the container

After the building, just run an instance of the container by executing:

```
docker run -it -d -p 8080:8080 ocr-cnh
```

You can check if the container is running accordingly by executing the `docker ps`.
Don't forget take a look at the logs (`docker logs {container_name_or_id}`)

### Ready to go!

At this point you're ready to go. Just access `http://localhost:8080` and you should see a nice and friendly form to test it :)

## Using the service

As said, this is a very simple service, with a even simpler use dynamic:
 - You send (upload within a POST `multipart/form-data` request) the document (CNH) image;
 - The service will return you a JSON with the document information (or not - it depends on the quality of the document and image)

### Usage example (in JavaScript)

The following code snippet examplifies how to use the API:

```javascript
import fetch from 'fetch';

let formData = new FormData();
let fileField = document.querySelector('input[type="file"]');
let file = fileField.files[0]

if (!file) alert('ERROR: Select a file.')

formData.append('file', file);

try {
    const rawResponse = await fetch('/cnh.json', { method: 'POST', body: formData });
    const response = rawResponse.json();
    console.log(response);
} catch (error) {
    console.error(error);
}
```

This request will return a JSON with the following format:
```json
{
	"nome": "XXXXXXXXXXXXXXX",
	"cpf": "XXXXXXXX",
	"dt_nasc": "XXXXXXXX",
	"rg": "XXXXXXXX",
	"rg_emissor": "XXXXXXXX",
	"rg_uf": "XXXXXXXX",
	"numero": "XXXXXXXX",
	"cidade": "XXXXXXXX",
	"uf": "XXXXXXXX",
	"pai": "XXXXXXXX",
	"mae": "XXXXXXXX",
	"emissao": "XXXXXXXX",
	"validade": "XXXXXXXX",
	"avatar": "XXXXXXXX"
}
```

# Contributors

[Contributors.](CONTRIBUTORS.md)