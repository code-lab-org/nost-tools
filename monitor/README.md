# NOS-T Manager Component

## Introduction

This node serves as the manager of simulation state and issues out the commands prefixed by `nost/manager/` as referenced in the NOS-T interface.

## Usage

### Deployment

The component is deployed on an AWS instance.

### Locally

To use the manager component, you need to have Docker. With Docker installed run:

```sh
$ docker-compose up --build
```

Once running, you will have a client and API interface at https://localhost/ and https://localhost/api/ respectively.

## Generating Documentation

Change directory into `./backend/docs/` and run:

```sh
$ sphinx-apidoc -f -o . ../nost
$ make html
```

To update the documentation. This documentation is then accessible at  `/api/docs/index.html`.
