# bitbucket-pipe-run-ecs-task

This pipe runs an ECS task in a cluster.

## YAML Definition

Add the following snippet to the `script` section of your `bitbucket-pipelines.yml` file:

```yaml
- pipe: docker://rubarbapp/pipe-run-ecs-task:latest
  variables:
    AWS_ROLE_ARN: arn:aws:iam::${AWS_ACCOUNT_ID}:role/OIDECSDeployerRole
    BITBUCKET_STEP_OIDC_TOKEN: $BITBUCKET_STEP_OIDC_TOKEN
    AWS_OIDC_ROLE_ARN: arn:aws:iam::${AWS_ACCOUNT_ID}:role/OIDECSDeployerRole
    AWS_DEFAULT_REGION: eu-central-1
    CLUSTER: <my-cluster>
    SERVICE: <my-service>
    TASK_DEFINITON: <my-task-definition>
```

## Variables

| Variable                  | Usage                                                        |          |
| ------------------------- | ------------------------------------------------------------ | -------- |
| AWS_DEFAULT_REGION        | Defaults to `eu-central-1`                                   | Optional |
| AWS_OIDC_ROLE_ARN         | The ARN of the role used for web identity federation or OIDC | Required |
| BITBUCKET_STEP_OIDC_TOKEN |  the OIDC Token                                              | Required |
| CLUSTER                   | The name of the ECS Cluster                                  | Required |
| SERVICE                   | The Service to run the task in                               | Required |
| TASK_DEFINITON            | The Name of the Task-Definiton                               | Required |

## IAM Permissions

```
data "aws_iam_policy_document" "ecs_deployer" {
  statement {
    effect = "Allow"
    actions = [
      "ecs:UpdateService",
      "ecs:DescribeTaskDefinition",
      "ecs:RegisterTaskDefinition",
      "ecs:ListTaskDefinitions"
    ]
    resources = [
      "*"
    ]
  }
}

/* OpenID Connect */
resource "aws_iam_role" "oid_ecs_deployer" {
  name               = "OIDECSDeployerRole"
  assume_role_policy = data.aws_iam_policy_document.oid_bitbucket.json
}

resource "aws_iam_role_policy" "oid_ecs_deployer" {
  name   = "OIDECSDeployerPolicy"
  role   = aws_iam_role.oid_ecs_deployer.id
  policy = data.aws_iam_policy_document.ecs_deployer.json
}
```
