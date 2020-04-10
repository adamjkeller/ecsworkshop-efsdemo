#!/bin/bash

cloudformation_outputs=$(aws cloudformation describe-stacks --stack-name ecsworkshop-efs-fargate-demo | jq .Stacks[].Outputs)
execution_role_arn=$(echo $cloudformation_outputs | jq -r '.[]| select(.ExportName | contains("ECSFargateEFSDemoTaskExecutionRoleARN"))| .OutputValue')
fs_id=$(echo $cloudformation_outputs | jq -r '.[]| select(.ExportName | contains("ECSFargateEFSDemoFSID"))| .OutputValue')
target_group_arn=$(echo $cloudformation_outputs | jq -r '.[]| select(.ExportName | contains("ECSFargateEFSDemoTGARN"))| .OutputValue')
private_subnets=$(echo $cloudformation_outputs | jq -r '.[]| select(.ExportName | contains("ECSFargateEFSDemoPrivSubnets"))| .OutputValue')
security_groups=$(echo $cloudformation_outputs | jq -r '.[]| select(.ExportName | contains("ECSFargateEFSDemoSecGrps"))| .OutputValue')
cluster_name="ECS-Fargate-EFS-Demo"
container_name="cloudcmd-rw"
task_definition_arn="arn:aws:ecs:us-west-2:333258026273:task-definition/cloudcmd-rw:9"

register_task_def() {
  sed "s|{{EXECUTIONROLEARN}}|$execution_role_arn|g;s|{{TASKROLEARN}}|$task_role_arn|g;s|{{FSID}}|$fs_id|g" task_definition.json > task_definition.automated
  task_definition_arn=$(aws ecs register-task-definition --cli-input-json file://"$PWD"/task_definition.automated | jq -r .taskDefinition.taskDefinitionArn)
}

create_service() {
  aws ecs create-service \
  --cluster $cluster_name \
  --service-name cloudcmd-rw \
  --task-definition "$task_definition_arn" \
  --load-balancers targetGroupArn="$target_group_arn",containerName="$container_name",containerPort=8000 \
  --desired-count 1 \
  --platform-version 1.4.0 \
  --launch-type FARGATE \
  --deployment-configuration maximumPercent=100,minimumHealthyPercent=0 \
  --network-configuration "awsvpcConfiguration={subnets=["$private_subnets"],securityGroups=["$security_groups"],assignPublicIp=DISABLED}"
}

#register_task_def
create_service

