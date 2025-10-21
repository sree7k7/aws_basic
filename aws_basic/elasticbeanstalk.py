from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
import aws_cdk as cdk
from constructs import Construct
import aws_cdk.aws_elasticloadbalancingv2_targets as elb_targets
from aws_cdk import aws_autoscaling as autoscaling

class ElasticBeanStalk(cdk.Stack):
    
    def __init__(self, scope: Construct, construct_id: str, vpc, instances, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        ## create a elastic load balancer
        