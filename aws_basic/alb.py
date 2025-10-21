from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
import aws_cdk as cdk
from constructs import Construct
import aws_cdk.aws_elasticloadbalancingv2_targets as elb_targets
from aws_cdk import aws_autoscaling as autoscaling

class AlbStack(cdk.Stack):
    
    def __init__(self, scope: Construct, construct_id: str, vpc, instances, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an Application Load Balancer
        alb = elbv2.ApplicationLoadBalancer(self, "MyAlb",
            vpc=vpc,
            internet_facing=True,
            load_balancer_name="myalb",
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=ec2.SecurityGroup(self, "AlbSecurityGroup",
                vpc=vpc,
                allow_all_outbound=True,
                security_group_name="alb-security-group"
            )
        )


## AutoScalingGroup

        # asg_template = ec2.LaunchTemplate(self, "MyLaunchTemplate",
        #     instance_type=ec2.InstanceType.of(
        #         ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO
        #     ),
        #     machine_image=ec2.MachineImage.latest_amazon_linux2023(
        #             edition=ec2.AmazonLinuxEdition.STANDARD,
        #         ),
        #     block_devices=[
        #             ec2.BlockDevice(
        #             device_name="/dev/xvda",
        #             volume=ec2.BlockDeviceVolume.ebs(
        #                 volume_size= 20,
        #                 volume_type= ec2.EbsDeviceVolumeType.GP3,
        #                 encrypted=True
        #             )
        #         )               
        #     ]
        # )
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
        # # Create an AutoScalingGroup
        asg = autoscaling.AutoScalingGroup(self, "MyAsg",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(
                    edition=ec2.AmazonLinuxEdition.STANDARD,
                ),
            min_capacity=1,
            max_capacity=6,
            desired_capacity=1,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            associate_public_ip_address=True,
            # user_data=ec2.UserData.custom(
            #     "#!/bin/bash\nyum install -y httpd\nsystemctl start httpd\nsystemctl enable httpd\necho 'Hello, World!' > /var/www/html/index.html"
            # ),
            user_data=user_data,
            block_devices=[autoscaling.BlockDevice(
                device_name="/dev/xvda",
                volume=autoscaling.BlockDeviceVolume.ebs(
                    volume_size=10,
                    volume_type=autoscaling.EbsDeviceVolumeType.GP3,
                    throughput=125
            )
            )
        ],
            ## automatic scaling
            cooldown=cdk.Duration.seconds(60),
            health_check=autoscaling.HealthCheck.ec2(grace=cdk.Duration.seconds(300)),
            update_policy=autoscaling.UpdatePolicy.rolling_update(
                pause_time=cdk.Duration.seconds(300),
                min_instances_in_service=1
            )
            
        )

        # Add a listener
        listener = alb.add_listener("Listener", port=80)

        # Add a target group
        # targets = [elb_targets.InstanceIdTarget(instance.instance_id) for instance in instances]
        targets = [asg]
        target_group = listener.add_targets(
            "alb", port=80, 
            targets=targets,
            stickiness_cookie_duration=cdk.Duration.seconds(60),
            )
                
        # Output ALB DNS name
        cdk.CfnOutput(self, "AlbDnsName", value=alb.load_balancer_dns_name)
        