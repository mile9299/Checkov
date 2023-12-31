from unittest import mock

import igraph
import pytest
from networkx import DiGraph

from checkov.common.graph.graph_builder import CustomAttributes
from checkov.kubernetes.image_referencer.manager import KubernetesImageReferencerManager
from checkov.common.images.image_referencer import Image
from checkov.kubernetes.runner import Runner as KubernetesRunner


@pytest.mark.parametrize("graph_framework", ['NETWORKX', 'IGRAPH'])
def test_extract_images_from_resources(graph_framework):
    # given
    resource = {
        "file_path_": "/pod.yaml",
        "__endline__": 16,
        "__startline__": 1,
        "spec": {
            "containers": [
                {
                    "name": "test-container",
                    "image": "nginx",
                },
            ],
        },
        "resource_type": "Pod",
    }
    if graph_framework == 'IGRAPH':
        graph = igraph.Graph()
        graph.add_vertex(
            name='1',
            block_type_='resource',
            resource_type=resource[
                CustomAttributes.RESOURCE_TYPE] if CustomAttributes.RESOURCE_TYPE in resource else None,
            attr=resource,
        )
    else:
        graph = DiGraph()
        graph.add_node(1, **resource)

    # when
    with mock.patch.dict('os.environ', {'CHECKOV_GRAPH_FRAMEWORK': graph_framework}):
        images = KubernetesImageReferencerManager(graph_connector=graph).extract_images_from_resources()

    # then
    assert images == [
        Image(
            file_path="/pod.yaml",
            name="nginx",
            start_line=1,
            end_line=16,
            related_resource_id="/pod.yaml:None",
        ),
    ]


@pytest.fixture()
def graph_resource_with_containers_and_init_containers():
    resource = {
        "file_path_": "/pod.yaml",
        "__endline__": 16,
        "__startline__": 1,
        "spec": {
            "initContainers": [
                {
                    "name": "test-container",
                    "image": "nginx",
                },
            ],
            "containers": [
                {
                    "name": "test-container",
                    "image": "nginx",
                },
            ],
        },
        "resource_type": "Pod",
    }
    graph = igraph.Graph()
    graph.add_vertex(
        name='duplicated_image',
        block_type_='resource',
        resource_type=resource[
            CustomAttributes.RESOURCE_TYPE] if CustomAttributes.RESOURCE_TYPE in resource else None,
        attr=resource,
    )
    return graph


def test_no_duplications_while_extracting_image_names(graph_resource_with_containers_and_init_containers: igraph.Graph):
    manager = KubernetesImageReferencerManager(graph_connector=graph_resource_with_containers_and_init_containers)
    images = manager.extract_images_from_resources()
    assert len(images) == 1
    image = images[0]
    assert image.name == 'nginx'
