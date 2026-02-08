resource "aws_autoscaling_group" "web-asg" {
    name = "web-app-asg"
    desired_capacity = 1
    min_size = 1
    max_size = 4

    vpc_zone_identifier = [
            aws_subnet.private_subnet_1.id,
            aws_subnet.private_subnet_2.id
    ]

    launch_template {
       id = aws_launch_template.app-lt.id
       version = "$Latest"
    }

    target_group_arns = [aws_lb_target_group.app_tg.arn]

  
    health_check_type         = "ELB"
    health_check_grace_period = 300

     tag {
        key                 = "Name"
         value               = "asg for app server"
        propagate_at_launch = true
    }


}

resource "aws_autoscaling_policy" "scale_out" {
    name = "cpu-scal-out"
    autoscaling_group_name = aws_autoscaling_group.web-asg.name
    adjustment_type = "ChangeInCapacity"
    scaling_adjustment = 1
    cooldown = 300

}

resource "aws_autoscaling_policy" "scale_in" {
    name = "cpu-scal-in"
    autoscaling_group_name = aws_autoscaling_group.web-asg.name
    adjustment_type = "ChangeInCapacity"
    scaling_adjustment = -1
    cooldown = 300
    
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name = "cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods = 2
  metric_name = "CPUUtilization"
  namespace = "AWS/EC2"
  period = 60
  statistic = "Average"
  threshold = 70


  alarm_actions = [aws_autoscaling_policy.scale_out.arn]


  dimensions = {
  AutoScalingGroupName = aws_autoscaling_group.web-asg.name
  }

}

resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name = "cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods = 3
  metric_name = "CPUUtilization"
  namespace = "AWS/EC2"
  period = 60
  statistic = "Average"
  threshold = 20


  alarm_actions = [aws_autoscaling_policy.scale_in.arn]


  dimensions = {
  AutoScalingGroupName = aws_autoscaling_group.web-asg.name
  }
}















