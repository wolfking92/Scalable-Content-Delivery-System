provider "aws" {
    region = "ap-south-1"
}

resource "aws_vpc" "myvpc_03" {
    cidr_block = "192.168.3.0/24"
    tags = {
      Name = "My Vpc 3"
    }
}

resource "aws_subnet" "public_subnet_1" {
    vpc_id = aws_vpc.myvpc_03.id
    availability_zone = "ap-south-1a"
    cidr_block = "192.168.3.0/26"
    tags = {
        Name = "Public Subnet 1"
    }
}

resource "aws_subnet" "public_subnet_2" {
    vpc_id = aws_vpc.myvpc_03.id
    availability_zone = "ap-south-1b"
    cidr_block = "192.168.3.64/26"
    tags = {
      Name = "Public Subnet 2"
    }

}

resource "aws_subnet" "private_subnet_1" {
    vpc_id = aws_vpc.myvpc_03.id
    availability_zone = "ap-south-1a"
    cidr_block = "192.168.3.128/26"
    tags = {
      Name = "Private Subnet 1"
    }
}

resource "aws_subnet" "private_subnet_2" {
    vpc_id = aws_vpc.myvpc_03.id
    availability_zone = "ap-south-1b"
    cidr_block = "192.168.3.192/26"
    tags = {
        Name = "Private Subnet 2"
    }
}

resource "aws_internet_gateway" "igw" {
    vpc_id = aws_vpc.myvpc_03.id
    tags = {
        Name = "for public internet"
    }
}

resource "aws_route_table" "rt_public" {
    vpc_id = aws_vpc.myvpc_03.id
    route = []
    tags = {
        Name = "Public Route Talbe"
    }
}

resource "aws_route_table" "rt_private" {
    vpc_id = aws_vpc.myvpc_03.id
    route = []
    tags = {
        Name = "Private Route Table"
    }

}

resource "aws_route" "pub" {
    route_table_id = aws_route_table.rt_public.id
    destination_cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id

}

resource "aws_route_table_association" "public_1" {
    subnet_id = aws_subnet.public_subnet_1.id
    route_table_id = aws_route_table.rt_public.id
}

resource "aws_route_table_association" "public_2" {
    subnet_id = aws_subnet.public_subnet_2.id
    route_table_id = aws_route_table.rt_public.id

}

resource "aws_eip" "ip" {
    domain = "vpc"

}

resource "aws_nat_gateway" "nat_gateway" {
    allocation_id = aws_eip.ip.id
    subnet_id = aws_subnet.public_subnet_1.id
    tags = {
        Nmae = "Nat Gateway"
    }
}

resource "aws_route" "pri" {
    route_table_id = aws_route_table.rt_private.id
    destination_cidr_block = "0.0.0.0/0"
    gateway_id = aws_nat_gateway.nat_gateway.id

}

resource "aws_route_table_association" "private_1" {
    subnet_id = aws_subnet.private_subnet_1.id
    route_table_id = aws_route_table.rt_private.id
}

resource "aws_route_table_association" "private_2" {
    subnet_id = aws_subnet.private_subnet_2.id
    route_table_id = aws_route_table.rt_private.id
}







