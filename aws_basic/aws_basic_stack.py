from aws_cdk import (
    # Duration,
    Stack
    # aws_sqs as sqs,
)
import aws_cdk.aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import Tags, aws_ec2 as ec2
import aws_cdk as cdk
import aws_cdk.aws_ssm as ssm

from constructs import Construct

class AwsBasicStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
    # vpc
        vpcx = ec2.Vpc(self, "VPC",
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
        
        # sg
        sg = ec2.SecurityGroup(self, "SecurityGroup",
            vpc=vpcx,
            description="Allow ssh access to ec2 instances",
            allow_all_outbound=True
        )
        
        ## allow ssh
        sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            "Allow ssh access from the world"
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
            resource_type=ec2.FlowLogResourceType.from_vpc(vpcx),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group, role),
            traffic_type=ec2.FlowLogTrafficType.ALL
        )
        # parameter = ssm.StringParameter.from_string_parameter_attributes(self, "UserString",
        #     parameter_name="/dnac/user/passwd"
        # ).string_value
        #######################user data############
        user_data = f'''
            #!/bin/bash      
            # sudo timedatectl set-timezone Europe/Copenhagen
            # sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a start
            # sudo yum update -y            
            sudo adduser sran
            sudo echo 'sran:Password@123' | sudo chpasswd
            rm /var/lib/cloud/instance/sem/config_scripts_user
            '''
        # user_data = ec2.UserData.for_linux()
        # user_data.add_commands(
        #     "sudo adduser sran",
        #     "echo 'sran:Password@123' | sudo chpasswd"
        # )
        
        ### Linux instance 1
        
        instance = ec2.Instance(
            self,
            'BackupInstance',
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.MICRO),
            vpc=vpcx,
            machine_image=ec2.MachineImage.latest_amazon_linux2023(
                cpu_type=ec2.AmazonLinuxCpuType.ARM_64,
                edition=ec2.AmazonLinuxEdition.STANDARD,
            ),
            credit_specification=ec2.CpuCredits.STANDARD,
            security_group=sg,
            role=role,
            user_data=ec2.UserData.custom(user_data),
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
        Tags.of(instance).add("OS", "Linux")
        # Tags.of(self).add("AppManagerCFNStackKey", "")
        
        
        ## Linux instance 2
        instance2 = ec2.Instance(
            self,
            'WindowsInstance',
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
            vpc=vpcx,
            machine_image=ec2.MachineImage.latest_windows(
                version=ec2.WindowsVersion.WINDOWS_SERVER_2022_ENGLISH_FULL_BASE,
            ),
            credit_specification=ec2.CpuCredits.STANDARD,
            security_group=sg,
            role=role,
            # user_data=ec2.UserData.custom(user_data),
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            block_devices=[
                ec2.BlockDevice(
                device_name="/dev/xvda",
                volume=ec2.BlockDeviceVolume.ebs(
                    volume_size= 15,
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
        Tags.of(instance2).add("OS", "Windows")
