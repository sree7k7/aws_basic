#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_basic.aws_basic_stack import AwsBasicStack
from aws_basic.alb import AlbStack

app = cdk.App()
basic_stack = AwsBasicStack(app, "AwsBasicStack")

# Use the first instance from the list
alb = AlbStack(app, "AlbStack", vpc=basic_stack.vpc, instance=basic_stack.instances[0])

app.synth()