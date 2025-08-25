# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import shutil
import tempfile
import time
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urlparse

import docker
from docker.errors import NotFound
from docker.models.containers import Container


READY_TIMEOUT_SEC = 20
CONTAINER_NAME_TPL = 'test-indico-pg-{pid}'
POSTGRES_IMAGE = 'docker.io/postgres:16'
DB_NAME = 'test'


def create_container_low_level(
    api_client: docker.APIClient, container_name: str, socket_dir: str, data_dir: str
) -> str:
    """Create a PostgreSQL container using the low-level docker-py API.

    :param api_client: The low-level Docker API client.
    :param container_name: The name to assign to the new container.
    :param socket_dir: Path to the host directory to mount as the PostgreSQL socket directory.
    :param data_dir: Path to the host directory to mount as the PostgreSQL data directory.

    :return: The ID of the created Docker container.
    :raises docker.errors.APIError: If the container creation fails.
    """
    # TODO: once https://github.com/docker/docker-py/issues/3351 is solved, use the high level API

    host_config = api_client.create_host_config(
        binds={
            socket_dir: {'bind': '/var/run/postgresql', 'mode': 'rw'},
            data_dir: {'bind': '/var/lib/postgresql/data', 'mode': 'rw'},
        }
    )

    # this is important so that the dirs above don't remain owned by some
    # phony container-specific user
    host_config['UsernsMode'] = 'keep-id'

    container_config = api_client.create_container(
        image=POSTGRES_IMAGE,
        name=container_name,
        # same here, we want everything in user space
        user=f'{os.getuid()}:{os.getgid()}',
        host_config=host_config,
        labels={'indico-test': 'true'},
        environment={'POSTGRES_USER': 'postgres', 'POSTGRES_PASSWORD': 'postgres', 'POSTGRES_DB': DB_NAME},
    )

    return container_config['Id']


def exec_in_container(container: Container, cmd: list[str] | str):
    """Execute a command inside a Docker container.

    :param container: The Docker container to run the command in.
    :param cmd: The command (and its arguments) to execute inside the container.
    :raises RuntimeError: If the command exits with a non-zero status code.
    """
    code, content = container.exec_run(cmd)
    if code != 0:
        raise RuntimeError(f'Command {cmd} failed: {content}')


def find_zombie_containers(docker_client: docker.DockerClient) -> set[Container]:
    """Find stopped test containers that can be safely removed.

    This function scans all Docker containers and returns a set of containers
    that have the 'exited' status and are labeled as Indico test containers
    (i.e., have the label 'indico_test' set to 'true'). These containers are
    considered "zombies" and can be cleaned up to free resources.

    :param docker_client: A DockerClient instance to query containers.
    :return: A set of Docker Container objects that are stopped Indico test containers.
    """
    zombies = set()

    for container in docker_client.containers.list(all=True):
        if (
            container.status == 'exited'
            and 'indico_test' in container.labels
            and container.labels['indico_test'] == 'true'
        ):
            zombies.add(container)

    return zombies


def kill_containers(containers: set[Container], *, warn: bool = False):
    """Kill and remove the specified Docker containers.

    This function stops and removes each container in the provided set. If a container is already stopped or removed,
    it will be skipped. Optionally, a warning can be emitted for each killed container.

    :param containers: A set of Docker Container objects to be killed and removed.
    :param warn: If True, emit a warning for each killed container.
    """
    for container in containers:
        # stop the container first, if it's still running
        if container.status in {'created', 'running', 'restarting', 'paused'}:
            container.stop()

        # It may happen that a container was created with --rm, in which case stopping it
        # will result int it being removed as well. Not likely, but it doesn't hurt to check
        try:
            container.wait(condition='not-running')
            container.remove()
            container.wait(condition='removed')
        except NotFound:
            # Container already removed, let's move on with our lives
            pass
        if warn:
            warnings.warn(f'Killed container {container.id}: {container.name}', stacklevel=0)


@contextmanager
def docker_postgresql() -> Iterator[str]:
    """Docker-based PostgreSQL server.

    This fixture runs a PostgreSQL server in a Docker container for tests.

    :raises ValueError: If ``INDICO_TEST_USE_DOCKER`` has an invalid scheme.
    :raises RuntimeError: If the container or PostgreSQL do not become ready in time.
    """
    container_name = CONTAINER_NAME_TPL.format(pid=os.getpid())
    use_docker = os.environ.get('INDICO_TEST_USE_DOCKER', None)
    if use_docker in {'1', 'true', 'yes'}:
        docker_client = docker.from_env()
    else:
        (scheme, _netloc, _path, _params, _query, _fragment) = urlparse(use_docker)
        if scheme not in {'unix', 'tcp'}:
            raise ValueError('Docker API URL should be unix:// or tcp://')

        docker_client = docker.DockerClient(base_url=use_docker)

    docker_client.images.pull(POSTGRES_IMAGE)

    socket_dir = tempfile.mkdtemp(prefix='indicotestpg.socket.')
    data_dir = tempfile.mkdtemp(prefix='indicotestpg.data.')

    # kill any possible zombie containers to avoid issues
    kill_containers(find_zombie_containers(docker_client), warn=True)

    try:
        container_id = create_container_low_level(docker_client.api, container_name, socket_dir, data_dir)
        docker_client.api.start(container_id)

        container = docker_client.containers.get(container_id)

        for __ in range(READY_TIMEOUT_SEC):
            container.reload()
            if container.status == 'running':
                break
            time.sleep(1)
        else:
            # Dump container logs into stdout
            print(container.logs().decode('utf8'))
            raise RuntimeError('Container did not become ready in time')

        for __ in range(READY_TIMEOUT_SEC):
            (code, _output) = container.exec_run(
                ['pg_isready', '-h', '/var/run/postgresql', '-U', 'postgres', '-d', DB_NAME]
            )
            if code == 0:
                break
            time.sleep(1)
        else:
            # Dump container logs into stdout
            print(container.logs().decode('utf8'))
            raise RuntimeError('PostgreSQL did not become ready in time')

        # Run DB setup commands using the UNIX socket inside the container
        exec_in_container(container, ['psql', DB_NAME, '-U', 'postgres', '-c', 'CREATE EXTENSION unaccent;'])
        exec_in_container(container, ['psql', DB_NAME, '-U', 'postgres', '-c', 'CREATE EXTENSION pg_trgm;'])

        yield f'postgresql://postgres:postgres@/{DB_NAME}?host={socket_dir}'
    finally:
        try:
            kill_containers({docker_client.containers.get(container_name)})
            zombies = find_zombie_containers(docker_client)
            kill_containers(zombies, warn=True)
        except NotFound:
            # not found, container was already removed (or never created)
            pass

        # delete temporary dirs
        shutil.rmtree(socket_dir)
        shutil.rmtree(data_dir)
