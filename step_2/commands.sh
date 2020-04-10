#!/bin/bash

execution_role_arn="arn:aws:iam::333258026273:role/ecsworkshop-efs-fargate-d-TaskExecutionRole250D253-UF9667SRIYY3"
#task_role_arn="arn:aws:iam::333258026273:role/testing-ecs-efs"
fs_id="fs-0d1453a7"
cluster_name="ECS-Fargate-EFS-Demo"
load_balancer="ecswo-ALBAE-3RHA8P87VOFR"
target_group_arn="arn:aws:elasticloadbalancing:us-west-2:333258026273:targetgroup/ECSDemoFargateEFS/11d5a1e2036151cb"
container_name="cloudcmd-rw"
private_subnet="subnet-0ec590c948ecc4bcd,subnet-04000b144902ada36"

register_task_def() {
  gsed "s|{{EXECUTIONROLEARN}}|$execution_role_arn|g;s|{{TASKROLEARN}}|$task_role_arn|g;s|{{FSID}}|$fs_id|g" task_definition.json > task_definition.automated
  task_definition_arn=$(aws ecs register-task-definition --cli-input-json file://"$(PWD)"/task_definition.automated | jq -r .taskDefinition.taskDefinitionArn)
}

create_service() {
  aws ecs create-service \
  --cluster $cluster_name \
  --service-name cloudcmd-rw \
  --task-definition "$task_definition_arn" \
  --load-balancers targetGroupArn="$target_group_arn",loadBalancerName="$load_balancer",containerName="$container_name",containerPort=8000 \
  --desired-count 1 \
  --platform-version 1.4 \
  --launch-type FARGATE \
  --deployment-configuration maximumPercent=100,minimumHealthyPercent=0 \
  --network-configuration awsvpcConfiguration={subnets=["$private_subnets"],securityGroups=[],assignPublicIp=string}
}

register_task_def

