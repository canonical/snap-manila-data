# snap-manila-data

This repository contains the source for the the OpenStack Manila Data snap.

This snap is designed to be used with a deployed OpenStack Control plane such
as delivered by Sunbeam.

## Getting Started

To get started with Manila Data, install the snap using snapd:

```bash
$ sudo snap install manila-data
```

The snap needs to be configured with RabbitMQ connection details:

```bash
$ sudo snap set manila-data \
    rabbitmq.url=rabbit://manila:supersecure@10.152.183.212:5672/openstack
```

And provide the database connection URL:

```bash
$ sudo snap set manila-data \
    database.url=mysql+pymysql://manila:password@10.152.183.210/manila
```

See "Configuration Reference" for full details.

## Configuration Reference

### database

* `database.url` Full connection URL to the database

### rabbitmq

* `rabbitmq.url` Full connection URL to RabbitMQ

### settings

* `settings.debug` (false) Enable debug log level
* `settings.enable-telemetry-notifications` (false) Enable telemetry notifications
