# pod
POD (PDF On Demand) is a microservice for generating PDFs out of HTML templates

## Docker image

POD is available as a Docker image. Example for docker-compose.yaml:

```
  my-project-pod:
    container_name: my-project-pod
    image: taitounited/pod:1.0.7
    restart: unless-stopped
    networks:
      - default
    ports:
      - "5000"
```

TODO: Move pod image registry to GitHub Packages.

## Usage

Make a POST request to `/` with the following fields:
* html
  * Should contain the HTML to be transformed as a string
* css (optional)
  * Should contain the CSS to be transformed as a string
