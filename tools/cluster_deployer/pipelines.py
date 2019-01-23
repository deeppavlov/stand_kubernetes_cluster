from deployer_stages import MakeFilesDeploymentStage, BuildImageDeploymentStage, DeleteKuberDeploymentStage
from deployer_stages import TestImageDeploymentStage, PushImageDeploymentStage
from deployer_stages import DeployKuberDeploymentStage, TestKuberDeploymentStage
from deployer_stages import PushToDockerHubDeploymentStage, DeleteImageDeploymentStage

all_stages = [MakeFilesDeploymentStage,
              DeleteImageDeploymentStage,
              BuildImageDeploymentStage,
              TestImageDeploymentStage,
              PushImageDeploymentStage,
              DeployKuberDeploymentStage,
              TestKuberDeploymentStage,
              PushToDockerHubDeploymentStage]

preset_pipelines = {
    'all': {
        'description': 'full cycle deployment: from making deploying files up to pushing to Docker Hub',
        'pipeline': [MakeFilesDeploymentStage,
                     DeleteImageDeploymentStage,
                     BuildImageDeploymentStage,
                     TestImageDeploymentStage,
                     PushImageDeploymentStage,
                     DeployKuberDeploymentStage,
                     TestKuberDeploymentStage,
                     PushToDockerHubDeploymentStage]
    },
    'all_up_kuber': {
        'description': 'full cycle deployment without pushing to Docker Hub',
        'pipeline': [MakeFilesDeploymentStage,
                     DeleteImageDeploymentStage,
                     BuildImageDeploymentStage,
                     TestImageDeploymentStage,
                     PushImageDeploymentStage,
                     DeployKuberDeploymentStage,
                     TestKuberDeploymentStage]
    },
    'all_from_docker': {
        'description': 'full cycle deployment without making deployment files',
        'pipeline': [DeleteImageDeploymentStage,
                     BuildImageDeploymentStage,
                     TestImageDeploymentStage,
                     PushImageDeploymentStage,
                     DeployKuberDeploymentStage,
                     TestKuberDeploymentStage,
                     PushToDockerHubDeploymentStage]
    },
    'from_docker_up_kuber': {
        'description': 'deployment cycle from building images up to deploying in Kubernetes',
        'pipeline': [DeleteImageDeploymentStage,
                     BuildImageDeploymentStage,
                     TestImageDeploymentStage,
                     PushImageDeploymentStage,
                     DeployKuberDeploymentStage,
                     TestKuberDeploymentStage]
    },
    'make_files': {
        'description': 'make deployment files',
        'pipeline': [MakeFilesDeploymentStage]
    },
    'build_docker': {'description': 'build and test images',
                     'pipeline': [DeleteImageDeploymentStage,
                                  BuildImageDeploymentStage,
                                  TestImageDeploymentStage]},
    'delete_docker': {
        'description': 'delete docker images',
        'pipeline': [DeleteImageDeploymentStage]
    },
    'create_kuber': {
        'description': 'deploy in Kubernetes and test',
        'pipeline': [DeployKuberDeploymentStage,
                     TestKuberDeploymentStage]
    },
    'delete_kuber': {
        'description': 'delete Kubernetes deployment',
        'pipeline': [DeleteKuberDeploymentStage]
    },
    'push_to_registry': {
        'description': 'push images to local registry',
        'pipeline': [PushImageDeploymentStage]
    },
    'push_to_docker_hub': {
        'description': 'push images to Docker Hub',
        'pipeline': [PushToDockerHubDeploymentStage]
    }
}
