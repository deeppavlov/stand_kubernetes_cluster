# Research image for demo stand

### Container handling instructions

Research container could be destroyed at any moment, so user should organize work in light of this circumstance.
Contents of home directory is saved.

After container re-creation `start.sh` script from user home is launched in background. User have to write this script
so that is starts work again. Checkpoints should be located at home too. 

New python packages should be installed to virtual environments: user have no permissions to install packages with pip
to container main `python`.

New packages could be installed to container with `sudo apt install <package_name>` (don't forget about `sudo apt
update` first). To save the state of containers there is a snapshot system:

```shell script
snapshot <command> [<snapshot_name>]
```

Commands:
* `new <snapshot_name>`: Create new container snapshot.
* `activate <snapshot_name>`: Make snapshot `<snapshot_name>` to be restored with every container restart.
* `remove <snapshot_name>`: Remove snapshot.
* `list`: Get snapshots list.
* `info`: Get active snapshot name.
* `reboot`: Restart container.

### Image deployment instructions:

#### Build image:

```shell script
cd stand_kubernetes_cluster/utils/research_spot
docker build -t research_img --build-arg NVIDIA_BASE_IMAGE=nvidia/cuda:10.0-devel-ubuntu18.04 \
                             --build-arg CUDNN_VERSION=7.6.2.24 \
                             --build-arg PYTHON_VERSION=3.7.4 .
```

#### Tag image and add it to registry:

```shell script
docker tag research_img kubeadm.ipavlov.mipt.ru:5000/stand/research_spot
docker push kubeadm.ipavlov.mipt.ru:5000/stand/research_spot
```

#### Create deployment:
* Add new config to `stand_kubernetes_cluster/tools/cluster_deployer/configs/models/research_spot.yaml`:

```yaml
research_spot_test:
  TEMPLATE: research_spot
  USER_NAME: test
  CLUSTER_SSH_PORT: 8096
  GPU_UNITS_NUM: 1
```

* Add user password to the separate file not tracked by `Git`:

```yaml
research_spot_test:
  PASSWORD: asdf
```

* Create new deployment:

```shell script
cd stand_kubernetes_cluster/tools/cluster_deployer
python run.py build -m research_spot_test -c ~/add.yaml
```
