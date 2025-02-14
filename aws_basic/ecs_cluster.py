from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch_actions as actions,
    Tags
)
from constructs import Construct
import aws_cdk as cdk

class EcsCluster(cdk.Stack):
    
    def __init__(self, scope: Construct, construct_id: str, vpcid: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
     # ECS Cluster
        # cluster = ecs.Cluster(self, "EcsCluster", vpc=vpcid)
        
        # Task Definition
        task_definition = ecs.FargateTaskDefinition(self, "TaskDef")
        container = task_definition.add_container("AppContainer",
            image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
            memory_limit_mib=512
        )
        container.add_port_mappings(ecs.PortMapping(container_port=80))
        
        # Fargate Serviceq
        service = ecs.FargateService(self, "FargateService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=2
        )
        
        # CloudWatch Alarm
        alarm = cloudwatch.Alarm(self, "TaskCountAlarm",
            metric=service.metric("RunningTaskCount"),
            threshold=10,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        # # SNS Topic
        # topic = sns.Topic(self, "AlarmTopic")
        
        # # Subscribe to the SNS Topic
        # topic.add_subscription(subs.EmailSubscription("info@example.com"))
        
        # # Add Alarm Action
        # alarm.add_alarm_action(actions.SnsAction(topic))