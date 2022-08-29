# /usr/bin/env python
from xmlrpc.server import CGIXMLRPCRequestHandler
import boto3
import configparser
import stat
import os
import time
from bitbucket_pipes_toolkit import Pipe

schema = {
    'AWS_DEFAULT_REGION': {
        'type': 'string',
        'required': False
    },
    'AWS_OIDC_ROLE_ARN': {
        'type': 'string',
        'required': True
    },
    'AWS_ROLE_ARN': {
        'type': 'string',
        'required': True
    },
    'BITBUCKET_STEP_OIDC_TOKEN': {
        'type': 'string',
        'required': True
    },
    'CLUSTER': {
        'type': 'string',
        'required': True
    },
    'SERVICE': {
        'type': 'string',
        'required': True
    },
    'TASK_DEFINITION': {
        'type': 'string',
        'required': True
    }
}


class RunECSTask(Pipe):

    def auth(self):
        web_identity_token = os.getenv('BITBUCKET_STEP_OIDC_TOKEN')
        random_number = str(time.time_ns())
        aws_config_directory = os.path.join(os.environ["HOME"], '.aws')
        oidc_token_directory = os.path.join(
            aws_config_directory, '.aws-oidc')

        os.makedirs(aws_config_directory, exist_ok=True)
        os.makedirs(oidc_token_directory, exist_ok=True)

        web_identity_token_path = os.path.join(
            f'{aws_config_directory}/.aws-oidc', f'oidc_token_{random_number}')
        with open(web_identity_token_path, 'w') as f:
            f.write(self.get_variable('BITBUCKET_STEP_OIDC_TOKEN'))
        os.chmod(web_identity_token_path, mode=stat.S_IRUSR)

        pipe.log_info('Web identity token file is created')

        aws_configfile_path = os.path.join(aws_config_directory, 'config')
        with open(aws_configfile_path, 'w') as configfile:
            config = configparser.ConfigParser()
            config['default'] = {
                'role_arn': self.get_variable('AWS_OIDC_ROLE_ARN'),
                'web_identity_token_file': web_identity_token_path
            }
            config.write(configfile)
        pipe.log_info(
            'Configured settings for authentication with assume web identity role')

    def run(self):
        super().run()
        self.auth()

        region = os.getenv('AWS_DEFAULT_REGION')
        cluster = os.getenv('CLUSTER')
        service = os.getenv('SERVICE')
        task_definition = os.getenv('TASK_DEFINITION')

        ecs = boto3.client('ecs', region_name=region)

        vpc_configuration = ecs.describe_services(cluster=cluster, services=[service])[
            'services'][0]['networkConfiguration']['awsvpcConfiguration']

        # get securitygroup and subnet-id
        security_group = vpc_configuration['securityGroups']
        subnet_id = vpc_configuration['subnets']

        # get taskdefinition ARN
        task_definition_arn = ecs.describe_task_definition(taskDefinition=task_definition)[
            'taskDefinition']['taskDefinitionArn']

        # start updater task
        ecs.run_task(
            cluster=cluster,
            launchType='FARGATE',
            taskDefinition=task_definition_arn,
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': subnet_id,
                    'securityGroups': security_group,
                    'assignPublicIp': 'DISABLED'
                }
            }
        )


pipe_metadata = {
    'name': 'pipe-run-ecs-task',
}

pipe = RunECSTask(pipe_metadata=pipe_metadata, schema=schema)
pipe.run()
