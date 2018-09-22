# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class HDInsightClusterTests(ScenarioTest):
    location = 'eastus'

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)  # Uses 'rg' kwarg
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster(self, storage_account_info):
        self._create_hdinsight_cluster(self._wasb_arguments(storage_account_info))

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)  # Uses 'rg' kwarg
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_minimum_arguments(self, storage_account_info):
        self._create_hdinsight_cluster(self._wasb_arguments(storage_account_info, specify_key=False, specify_container=False))

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_resize(self, storage_account_info):
        self._create_hdinsight_cluster(self._wasb_arguments(storage_account_info))

        resize_cluster_format = 'az hdinsight cluster resize -n {name} -g {rg} --workernode-count 2'
        self.cmd(resize_cluster_format, checks=[
            self.check('properties.clusterState', 'Running'),
            self.check("properties.computeProfile.roles[?name=='workernode'].targetInstanceCount", '2')
        ])

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_kafka(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._kafka_arguments()
        )

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_kafka_with_optional_disk_args(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._kafka_arguments(),
            HDInsightClusterTests._optional_data_disk_arguments()
        )

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_rserver(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._rserver_arguments()
        )

    def _create_hdinsight_cluster(self, *additional_create_arguments):
        self.kwargs.update({
            'loc': self.location,
            'name': self.create_random_name(prefix='hdicli-', length=16),
            'http-user': 'admin',
            'http-password': 'Password1!',
            'ssh-user': 'sshuser',
            'ssh-password': 'Password1!'
        })

        create_cluster_format = 'az hdinsight create -n {name} -g {rg} -l {loc} ' \
                                '-p {http-password} ' \
                                + ' '.join(additional_create_arguments)
        self.cmd(create_cluster_format, checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.clusterState', 'Running'),
            self.check("properties.computeProfile.roles[?name=='headnode'].osProfile.linuxOperatingSystemProfile.username", 'sshuser')
        ])

        self.cmd('az hdinsight cluster show -n {name} -g {rg}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.clusterState', 'Running')
        ])

    @staticmethod
    def _wasb_arguments(storage_account_info, specify_key=True, specify_container=True):
        storage_account_name, storage_account_key = storage_account_info
        storage_account_key = storage_account_key.strip()

        key_args = '--storage-account-key "{}"'.format(storage_account_key) if specify_key else ""
        container_args = '--storage-default-container {}'.format('default') if specify_container else ""

        return '--storage-account {}.blob.core.windows.net {} {}'\
            .format(storage_account_name, key_args, container_args)

    @staticmethod
    def _kafka_arguments():
        return '-t {} --workernode-data-disks-per-node {}'.format('kafka', '4')

    @staticmethod
    def _optional_data_disk_arguments():
        return '--workernode-data-disk-storage-account-type {} --workernode-data-disk-size {}'.format('Standard_LRS', '1023')

    @staticmethod
    def _rserver_arguments():
        return '-t {} --edgenode-size {}'.format('rserver', 'large')


