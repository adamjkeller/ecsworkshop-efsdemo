from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_efs as efs,
    core
)

from os import getenv


class ECSFargateEFSDemo(core.Stack):

    def __init__(self, scope: core.Stack, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ## VPC and ECS Cluster ##
        self.vpc = ec2.Vpc(self, "VPC", max_azs=2)

        self.ecs_cluster = ecs.Cluster(
            self, "ECSCluster",
            cluster_name="ECS-Fargate-EFS-Demo",
            vpc=self.vpc
        )
        ## End VPC and ECS Cluster ##

        ## Load balancer for Wordpress container ##
        self.frontend_sec_grp = ec2.SecurityGroup(
            self, "FrontendIngress",
            vpc=self.vpc,
            allow_all_outbound=True,
            description="Frontend Ingress All port 80",
        )

        self.load_balancer = elbv2.ApplicationLoadBalancer(
            self, "ALB",
            security_group=self.frontend_sec_grp,
            internet_facing=True,
            vpc=self.vpc
        )

        self.target_group = elbv2.ApplicationTargetGroup(
            self, "ALBTG",
            port=8000,
            target_group_name="ECSDemoFargateEFS",
            vpc=self.vpc,
            target_type=elbv2.TargetType.IP
        )
        
        self.load_balancer.add_listener(
            "FrontendListener",
            default_target_groups=[
                self.target_group
            ],
            port=80
        )
        ## End Load balancer ##

        ## EFS Setup ##
        self.efs_sec_grp = ec2.SecurityGroup(
            self, "EFSSecGrp",
            vpc=self.vpc,
            description="Allow access to self on NFS Port",
        )

        self.efs_sec_grp.connections.allow_from(
            other=self.efs_sec_grp,
            port_range=ec2.Port(protocol=ec2.Protocol.TCP, string_representation="Self", from_port=2049, to_port=2049)
        )

        self.shared_fs = efs.EfsFileSystem(
            self, "SharedFS",
            vpc=self.vpc,
            security_group=self.efs_sec_grp,
        )
        ## End EFS Setup ##

        ## TODO: IAM Role to access EFS access points for task ##

        # Task execution role
        self.task_execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
            description="Task execution role for ecs services",
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(self, 'arn', managed_policy_arn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy')
            ]
        )

        ## END IAM ##

        # Cloudformation Outputs
        core.CfnOutput(
            self, "ExecutionRoleARN",
            value=self.task_execution_role.role_arn,
            export_name="ECSFargateEFSDemoTaskExecutionRoleARN"
        )

        core.CfnOutput(
            self, "EFSID",
            value=self.shared_fs.file_system_id,
            export_name="ECSFargateEFSDemoFSID"
        )

        core.CfnOutput(
            self, "LBName",
            value=self.load_balancer.load_balancer_name,
            export_name="ECSFargateEFSDemoLBName"
        )

        core.CfnOutput(
            self, "TargetGroupArn",
            value=self.target_group.target_group_arn,
            export_name="ECSFargateEFSDemoTGARN"
        )

        core.CfnOutput(
            self, "VPCPrivateSubnets",
            value=",".join([x.subnet_id for x in self.vpc.private_subnets]),
            export_name="ECSFargateEFSDemoPrivSubnets"
        )

        core.CfnOutput(
            self, "SecurityGroups",
            value=",".join([x.subnet_id for x in self.vpc.private_subnets]),
            export_name="ECSFargateEFSDemoPrivSubnets"
        )


app = core.App()

_env = core.Environment(account=getenv('CDK_DEFAULT_ACCOUNT'), region=getenv('AWS_DEFAULT_REGION'))

ECSFargateEFSDemo(app, "ecsworkshop-efs-fargate-demo", env=_env)

app.synth()
