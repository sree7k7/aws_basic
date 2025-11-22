from typing import Optional
from constructs import Construct

from aws_cdk import (
    Stack,
    Duration,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch as cw,
    aws_cloudwatch_actions as cw_actions,
)


class SnsAlertStack(Stack):
    """
    CDK Stack that creates an SNS Topic for alerts and a helper to attach CloudWatch alarms to it.

    Usage:
      stack = SnsAlertStack(app, "SnsAlertStack", alert_email="ops@example.com")
      metric = cw.Metric(namespace="MyApp", metric_name="ErrorCount", period=Duration.minutes(1))
      stack.create_alarm_for_metric(metric, alarm_name="HighErrorRate", threshold=10, evaluation_periods=3)
    """

    def __init__(self, scope: Construct, construct_id: str, alert_email: Optional[str] = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SNS Topic for alerts
        self.alerts_topic = sns.Topic(
            self,
            "AlertsTopic",
            display_name="ApplicationAlerts",
            topic_name=f"{construct_id}-alerts",
        )
        
        # create subscription to email for alerts
        subscription = sns.Subscription(
            self,
            "EmailSubscription",
            topic=self.alerts_topic,
            protocol=sns.SubscriptionProtocol.EMAIL,
            endpoint="sree7k7@gmail.com"
        )

        

        # Optional email subscription (provide a real email when deploying)
        if alert_email:
            self.alerts_topic.add_subscription(subs.EmailSubscription(alert_email))

    def create_alarm_for_metric(
        self,
        metric: cw.IMetric,
        alarm_name: str,
        threshold: float,
        evaluation_periods: int = 1,
        comparison_operator: cw.ComparisonOperator = cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
        treat_missing_data: cw.TreatMissingData = cw.TreatMissingData.NOT_BREACHING,
    ) -> cw.Alarm:
        """
        Create a CloudWatch alarm for the given metric and attach the SNS topic as the alarm action.

        Returns the created Alarm instance.
        """
        alarm = cw.Alarm(
            self,
            alarm_name,
            alarm_name="cpu-test" + alarm_name,
            metric=metric,
            threshold=threshold,
            evaluation_periods=evaluation_periods,
            comparison_operator=comparison_operator,
            treat_missing_data=treat_missing_data,
        )

        # Send alarm notifications to SNS topic
        alarm.add_alarm_action(cw_actions.SnsAction(self.alerts_topic))

        return alarm


# Example stack instantiation for use in app.py (uncomment when used in real CDK app):
# from aws_cdk import App, Environment
# app = App()
# SnsAlertStack(app, "SnsAlertStack", alert_email="ops@example.com")
# app.synth()