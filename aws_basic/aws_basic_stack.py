from aws_cdk import aws_ec2 as ec2, aws_iam as iam, aws_logs as logs, aws_elasticloadbalancingv2 as elb, Tags

import aws_cdk.aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import Tags, aws_ec2 as ec2
import aws_cdk as cdk
import aws_cdk.aws_ssm as ssm
import aws_cdk.aws_elasticloadbalancingv2 as elb
import aws_cdk.aws_elasticloadbalancingv2_targets as elb_targets
import aws_cdk.aws_cloudwatch as cloudwatch
import aws_cdk.aws_sns as sns
import aws_cdk.aws_sns_subscriptions as subs
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
import aws_cdk.aws_events_targets as events_targets
from aws_cdk.aws_cloudwatch_actions import SnsAction
from aws_cdk.aws_elasticloadbalancingv2 import ListenerAction
from constructs import Construct
from aws_cdk import CfnOutput

class AwsBasicStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
    # vpc
        self.vpc = ec2.Vpc(self, "VPC",
            max_azs=3,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                ),
            ]
        )
        
        # export vpc id vaue to other stacks
        vpcid = CfnOutput(self, "vpc_id",
            value=self.vpc.vpc_id,
            description="vpc id of the stack"
        )
        
        print(f"VPC-----ID: {vpcid}")        
        
        # sg
        sg = ec2.SecurityGroup(self, "SecurityGroup",
            vpc=self.vpc,
            security_group_name="EC2SecurityGroup",
            description="Allow ssh access to ec2 instances",
            allow_all_outbound=True
        )
        
        ## allow ssh
        sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            "Allow ssh access from the world"
        )
        
        sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow http access from the world"
        )
                       
        ## icmp traffic
        sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.icmp_type(8),
            "Allow icmp access from the world"
        )
        
        role = iam.Role(
            self,
            "BackupRole",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchAgentAdminPolicy'),
            ],
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"),
                iam.ServicePrincipal("s2svpn.amazonaws.com"),
                iam.ServicePrincipal("vpc-flow-logs.amazonaws.com")
            )
        )
        log_group = logs.LogGroup(
            self, 
            "VPCFlowLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=cdk.RemovalPolicy.DESTROY
            )
        ec2.FlowLog(
            self, 
            "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(self.vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group, role),
            traffic_type=ec2.FlowLogTrafficType.ALL
        )
        # parameter = ssm.StringParameter.from_string_parameter_attributes(self, "UserString",
        #     parameter_name="/dnac/user/passwd"
        # ).string_value
        #######################user data############
        user_data_script = '''
        sudo yum update -y           
        sudo yum install -y httpd
        sudo systemctl start httpd
        sudo systemctl enable httpd
        sudo echo "<h1> Hello from $(hostname -f)</h1>" > /var/www/html/index.html 
        rm /var/lib/cloud/instance/sem/config_scripts_user
        '''
        
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(user_data_script)
        
        ### Linux instance 1
        self.instances = []
        for i in range(2):
            instance = ec2.Instance(
                self,
                f'BackupInstance{i}',
                instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3_AMD, ec2.InstanceSize.SMALL),
                vpc=self.vpc,
                machine_image=ec2.MachineImage.latest_amazon_linux2023(
                    edition=ec2.AmazonLinuxEdition.STANDARD,
                ),
                security_group=sg,
                role=role,
                user_data=user_data,
                # maintenance_options=ec2.InstanceMaintenanceOptions(
                # auto_recovery=ec2.InstanceAutoRecovery.DEFAULT
                #         ),
                user_data_causes_replacement=True,
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PUBLIC
                ),
                block_devices=[
                    ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size= 10,
                        volume_type= ec2.EbsDeviceVolumeType.GP3,
                        encrypted=True
                    )
                ),
                #     ec2.BlockDevice(
                #     device_name="/dev/sdg",
                #     volume=ec2.BlockDeviceVolume.ebs(
                #         volume_size= config['server']['volume_size'],
                #         volume_type= ec2.EbsDeviceVolumeType.GP3,
                #         encrypted=True
                #     )
                # )                
                ]
            )
            self.instances.append(instance)
            # Tags.of(self.instance).add("OS", "Linux")
            # Tags.of(self).add("AppManagerCFNStackKey", "")
          
        # ## windows instance 2
        # instance2 = ec2.Instance(
        #     self,
        #     'WindowsInstance',
        #     instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
        #     vpc=vpc,
        #     machine_image=ec2.MachineImage.latest_windows(
        #         version=ec2.WindowsVersion.WINDOWS_SERVER_2022_ENGLISH_FULL_BASE,
        #     ),
        #     security_group=sg,
        #     role=role,
        #     vpc_subnets=ec2.SubnetSelection(
        #         subnet_type=ec2.SubnetType.PUBLIC
        #     ),
        #     block_devices=[
        #         ec2.BlockDevice(
        #         device_name="/dev/xvda",
        #         volume=ec2.BlockDeviceVolume.ebs(
        #             volume_size= 15,
        #             volume_type= ec2.EbsDeviceVolumeType.GP3,
        #             encrypted=True
        #         )
        #     ),                
        #     ]
        # )
        # Tags.of(instance2).add("OS", "Windows")


## Application load balancer

    #     ## alb security group
    #     lb_sg = ec2.SecurityGroup(self, "ALBSecurityGroup",
    #         vpc=vpc,
    #         description="Allow http access to ALB",
    #         allow_all_outbound=True
    #     )
    #     lb_sg.add_ingress_rule(
    #         ec2.Peer.any_ipv4(),
    #         ec2.Port.tcp(80),
    #         "Allow http access from the world"
    #     )

    #    # Application Load Balancer
    #     lb = elb.ApplicationLoadBalancer(
    #         self, "LB",
    #         vpc=vpc,
    #         internet_facing=True,
    #         security_group=lb_sg
    #     )
        
    #     # # Listener and target group
    #     listener = lb.add_listener("Listener", port=80)
    #     listener.add_targets(
    #         "Target",
    #         port=80,
    #         targets=[elb_targets.InstanceIdTarget(instance.instance_id)],
    #         health_check=elb.HealthCheck(
    #             path="/",
    #             interval=cdk.Duration.seconds(60),
    #             timeout=cdk.Duration.seconds(30)                
    #         )
    #     )
    #     lb.connections.allow_from_any_ipv4(ec2.Port.tcp(80), "Internet access to ALB")
        
    #     ## allow alb security group to access ec2 instances
    #     sg.add_ingress_rule(
    #         lb_sg,
    #         ec2.Port.tcp(80),
    #         "Allow http access from ALB"
    #     )
    
    
    ## fargate service
    
    # # ECS Cluster
    #     cluster = ecs.Cluster(self, "EcsCluster", vpc=vpc)
        
    #     # Task Definition
    #     task_definition = ecs.FargateTaskDefinition(self, "TaskDefinition")
    #     container = task_definition.add_container("AppContainer",
    #         ## add nginx image,             
    #         image=ecs.ContainerImage.from_registry("nginx"),
    #         memory_limit_mib=512,
    #         cpu=256
    #     )
    #     ## IAM role used by the ECS service has the necessary permissions to publish to the SNS topic.
        
    #     topic_policy = iam.PolicyStatement(
    #         effect=iam.Effect.ALLOW,
    #         actions=["sns:*"],
    #         resources=["*"]
    #     )
    #     task_definition.task_role.add_to_policy(topic_policy)
        
    #     task_definition.add_to_task_role_policy(
    #         iam.PolicyStatement(
    #             effect=iam.Effect.ALLOW,
    #             actions=["ecs:RunTask"],
    #             resources=["*"]
    #         )
    #     )
        
    #     container.add_port_mappings(ecs.PortMapping(container_port=80))
    #     container.add_port_mappings(ecs.PortMapping(container_port=443))
        
    #     # Fargate Service
    #     service = ecs.FargateService(self, "FargateService",
    #         cluster=cluster,
    #         service_name="CustomFargateService",
    #         task_definition=task_definition,
    #         assign_public_ip=True,
    #         desired_count=5,
    #         vpc_subnets=ec2.SubnetSelection(
    #             subnet_type=ec2.SubnetType.PUBLIC
    #         ),
    #         security_groups=[sg]
    #     )
        
        # # CloudWatch Alarm
        # alarm = cloudwatch.Alarm(self, "TaskCountAlarm",
        #     metric=service.metric("RunningTaskCount"),
        #     threshold=2,
        #     evaluation_periods=1,
        #     datapoints_to_alarm=1,
        #     comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        # )
        
        # SNS Topic
        # topic = sns.Topic(self, 
        #                 "AlarmTopic",
        #                 display_name="AlarmTopic",        
        #         )
        
    #     # # Subscribe to the SNS Topic
    #     topic.add_subscription(subs.EmailSubscription("sree7k7@gmail.com"))
               
    #     ## create event rule when desired count in fargate service increases. if desired count is more than 2, then send email
    #     rule = events.Rule(self, "Rule",
    #         event_pattern=events.EventPattern(
    #             source=["aws.ecs"],
    #             detail_type=["ECS Task State Change"],
    #             detail={
    #                 "clusterArn": [cluster.cluster_arn],
    #                 "lastStatus": ["RUNNING"],
    #                 "desiredStatus": ["RUNNING"]
    #             }
    #         )
    #     )
        
    #     ## Add sns topic as target to the rule
    #     rule.add_target(events_targets.SnsTopic(
    #             topic=topic,
    #             message=events.RuleTargetInput.from_text(
    #                     f"Tasks count for {service.service_name} is increasing..."
    # )
    #         )
    #     )
    #             # # Add Alarm Action
    #     alarm.add_alarm_action(SnsAction(topic))