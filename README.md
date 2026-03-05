# snap-manila-data

This repository contains the source for the OpenStack Manila Data snap.

The **manila-data** daemon is part of [OpenStack Manila](https://docs.openstack.org/manila/latest/),
the Shared Filesystems service. It handles data-intensive operations such as:

- **Share migration** — both driver-assisted and host-assisted migration of
  data between share backends.
- **Share creation from snapshots** — copying data when creating a new share
  from an existing snapshot requires a data transfer.

The snap packages the upstream `manila-data` binary together with Ceph
(`ceph-common`) and NFS support, manages its configuration files via Jinja2
templating, and runs the service as a strictly-confined snap daemon.

This snap is designed to be used with a deployed OpenStack control plane such
as delivered by [Sunbeam](https://canonical-openstack.readthedocs-hosted.com/en/latest/how-to/features/shared-filesystem/).

## Getting Started

### Installation

Install the snap from the Snap Store:

```bash
sudo snap install manila-data
```

### Required configuration

The service will not start until the database and message queue connections are
provided:

```bash
sudo snap set manila-data \
    database.url=mysql+pymysql://manila:password@10.152.183.210/manila

sudo snap set manila-data \
    rabbitmq.url=rabbit://manila:supersecure@10.152.183.212:5672/openstack
```

Once both values are set the `configure` hook will render the configuration
files and start (or restart) the `manila-data` daemon automatically.

### Verifying the service

```bash
sudo snap services manila-data
```

Logs are written to syslog. You can also inspect the snap-specific log:

```bash
sudo snap logs manila-data
```

## Configuration Reference

All options are set with `snap set manila-data <key>=<value>` and read with
`snap get manila-data <key>`.

### database

| Key | Description |
|---|---|
| `database.url` | Full SQLAlchemy connection URL to the Manila database (e.g. `mysql+pymysql://user:pass@host/manila`) |

### rabbitmq

| Key | Description |
|---|---|
| `rabbitmq.url` | Full connection URL to the RabbitMQ broker (e.g. `rabbit://user:pass@host:5672/openstack`) |

### settings

| Key | Default | Description |
|---|---|---|
| `settings.debug` | `false` | Enable debug-level logging |
| `settings.enable-telemetry-notifications` | `false` | Enable Oslo messaging notifications for telemetry (Ceilometer) |

## Snap Interfaces

The snap uses the following [interfaces](https://snapcraft.io/docs/supported-interfaces):

| Plug | Purpose |
|---|---|
| `network` | Outbound network access (database, RabbitMQ) |
| `network-bind` | Listen for incoming connections |
| `mount-observe` | Observe mount points on the host |
| `nfs-mount` | Mount and unmount NFS shares |

## Building from source

The snap is built with [Snapcraft](https://snapcraft.io/docs/snapcraft-overview):

```bash
snapcraft
```

### Running tests

```bash
tox -e py312    # unit tests
tox -e lint     # linting
```

## Contributing

This project is open source under the [Apache 2.0 license](LICENSE).
Contributions are welcome — please open an issue or submit a pull request.
