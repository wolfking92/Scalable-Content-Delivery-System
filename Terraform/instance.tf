resource "aws_instance" "first" {
ami = "ami-00ca570c1b6d79f36"
instance_type = "t3.micro"
availability_zone = "ap-south-1a"
associate_public_ip_address = true

subnet_id =  aws_subnet.public_subnet_1.id
key_name = "host1"
vpc_security_group_ids = [aws_security_group.web_sg.id]


tags = {
  Name = "for bastion host"
}


}