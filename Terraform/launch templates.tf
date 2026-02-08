resource "aws_launch_template" "app-lt" {
    name_prefix = "Lumina-Web-App"
    image_id = "ami-0e2bffbb45c29b879"
    instance_type = "t3.micro"
    key_name = "nn"

    network_interfaces {
      security_groups = [aws_security_group.app_sg.id]
      associate_public_ip_address = false
    }


    iam_instance_profile {
    name = "s3-access-get" 
    }


    user_data = base64encode(<<-EOF
      #!/bin/bash
      dnf install nfs-utils -y
      mkdir -p /home/ec2-user/web_app/instance
      
      # NEW MOUNT COMMAND WITH CACHE DISABLING
      mount -t nfs -o rw,sync,noac 192.168.3.53:/home/ec2-user/web_app/instance /home/ec2-user/web_app/instance
      
      systemctl restart webapp
    EOF
  )

   tag_specifications  {
    resource_type = "instance"
    tags = {
      Name = "launch template for app sg"
    }
  }
}
