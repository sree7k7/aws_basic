from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
import aws_cdk as cdk
from constructs import Construct
import aws_cdk.aws_elasticloadbalancingv2_targets as elb_targets

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
                allow_all_outbound=True
            )
            
        )

        # Add a listener
        listener = alb.add_listener("Listener", port=80)

        # Add a target group
        targets = [elb_targets.InstanceIdTarget(instance.instance_id) for instance in instances]
        target_group = listener.add_targets("alb", port=80, targets=targets)
        # target_group = listener.add_targets("alb", port=80, targets=[elb_targets.InstanceIdTarget(instance.instance_id)])
        
        # Allow inbound traffic from ALB to EC2 instance on port 80
        # instance.connections.allow_from(alb, ec2.Port.tcp(80), "Allow HTTP traffic from ALB")
        # instance.connections.allow_from(alb, ec2.Port.tcp(80), "Allow HTTP traffic from ALB")
        
        # # Allow inbound traffic from ALB to EC2 instance on port 443
        # instance.connections.allow_from(alb, ec2.Port.tcp(443), "Allow HTTPS traffic from ALB")
        
        # Output ALB DNS name
        cdk.CfnOutput(self, "AlbDnsName", value=alb.load_balancer_dns_name)
