import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_basic.aws_basic_stack import AwsBasicStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_basic/aws_basic_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsBasicStack(app, "aws-basic")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
