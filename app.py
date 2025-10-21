#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_basic.aws_basic_stack import AwsBasicStack
from aws_basic.alb import AlbStack

app = cdk.App()
basic_stack = AwsBasicStack(app, "AwsBasicStack")
# alb = AlbStack(app, "AlbStack", vpc=basic_stack.vpc, instances=basic_stack.instances)


app.synth()