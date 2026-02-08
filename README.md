# Scalable-Content-Delivery-System
Platform where users can upload large media files and consume them smoothly across devices. Handle growing user traffic and storage needs without performance degradation or excessive costs

A complete implementation of a Content Delivery which is highly available, auto-scaling web application infrastructure on AWS. This project demonstrates enterprise-level architecture with automatic scaling, load balancing, shared storage, and multi-tier security design.

## What This Project Does

This is a production-ready deployment of a Content Delivery web application that automatically scales based on traffic demand. The infrastructure uses an Application Load Balancer to distribute traffic across multiple application servers running in private subnets. When CPU usage increases, new servers automatically spin up. When traffic decreases, extra servers shut down to save costs.

The application uses a shared NFS storage system for persistent data, allowing all application servers to access the same files and database.

 ## Architecture Overview

### AWS Cloud - Region: ap-south-1 (Mumbai)

**VPC Configuration:**
- VPC Name: `my vpc`
- CIDR Range: `192.168.1.0/24`
- Total Available IPs: 256 addresses

**Subnets Across Two Availability Zones:**

Public Subnets (for ALB and Bastion):
- Public Subnet 1: `192.168.1.0/26` in ap-south-1a
- Public Subnet 2: `192.168.1.64/26` in ap-south-1b

Private Subnets (for Application Servers):
- Private Subnet 1: `192.168.1.128/26` in ap-south-1a
- Private Subnet 2: `192.168.1.192/26` in ap-south-1b



### Complete Traffic Flow

```
Internet Users
      ↓
Internet Gateway (IGW)
      ↓
Application Load Balancer (ALB)
- Listener: HTTP:80
- Subnets: Public Subnet 1 + Public Subnet 2
- Security Group: alb_sg (Port 80 from anywhere)
      ↓
Target Group (app-tg)
- Protocol: HTTP
- Port: 5000
- Health Check: / on port 5000
      ↓
Auto Scaling Group (web-app_asg)
- Min: 1, Desired: 1, Max: 4
- Launch Template: web_app_2
- Subnets: Private Subnet 1 + Private Subnet 2
      ↓
EC2 Instances (App Servers)
- Instance Type: t3.micro
- Security Group: app_sg (Port 5000 from ALB only)
- Application: Flask on port 5000
      ↓
NFS Master Server (Shared Storage)
- Stores SQLite database and uploaded files
- Mounted on all app servers
      ↓
NAT Gateway (for outbound internet)
      ↓
Internet Gateway
```


## Technology Stack

**Infrastructure as Code:**
- Terraform - Complete infrastructure automation
- AWS Provider - Cloud resource management

**Cloud Infrastructure:**
- Amazon VPC - Network isolation and segmentation
- EC2 Instances - t3.micro (2 vCPU, 1 GB RAM)
- Application Load Balancer - Layer 7 load balancing
- Auto Scaling Group - Dynamic capacity management
- NAT Gateway - Secure outbound internet access
- Internet Gateway - Inbound traffic routing
- CloudWatch - Monitoring and alarms

**Application Stack:**
- Python 3.9 - Programming language
- Flask - Web framework
- Gunicorn - WSGI HTTP server
- SQLite - Database (shared via NFS)
- NFS - Network file system for shared storage
- Amazon Linux 2 - Operating system

**Storage Architecture:**
- NFS Master Server - Centralized file storage
- Shared SQLite Database - Application data
- File uploads storage - User-generated content

## Infrastructure Components

### VPC and Network Architecture

**VPC Design:**
```
VPC CIDR: 192.168.1.0/24 (256 total IPs)
├── Public Subnet 1:  192.168.1.0/26    (62 usable IPs) - ap-south-1a
├── Public Subnet 2:  192.168.1.64/26   (62 usable IPs) - ap-south-1b
├── Private Subnet 1: 192.168.1.128/26  (62 usable IPs) - ap-south-1a
└── Private Subnet 2: 192.168.1.192/26  (62 usable IPs) - ap-south-1b
```

**Routing Configuration:**

*Public Route Table:*
- Local: 192.168.1.0/24 → VPC
- Internet: 0.0.0.0/0 → Internet Gateway
- Associated: Public Subnet 1, Public Subnet 2

*Private Route Table:*
- Local: 192.168.1.0/24 → VPC
- Internet: 0.0.0.0/0 → NAT Gateway
- Associated: Private Subnet 1, Private Subnet 2

### Security Groups Architecture

The infrastructure uses three security groups following the principle of least privilege:

**1. alb_sg - Application Load Balancer Security Group**
```
Purpose: Control traffic to the load balancer

Inbound Rules:
┌──────────────┬──────┬─────────────┬──────────────────────┐
│ Protocol     │ Port │ Source      │ Description          │
├──────────────┼──────┼─────────────┼──────────────────────┤
│ HTTP         │ 80   │ 0.0.0.0/0   │ Internet traffic     │
└──────────────┴──────┴─────────────┴──────────────────────┘

Outbound Rules:
┌──────────────┬──────┬─────────────┬──────────────────────┐
│ Protocol     │ Port │ Destination │ Description          │
├──────────────┼──────┼─────────────┼──────────────────────┤
│ All          │ All  │ 0.0.0.0/0   │ All outbound         │
└──────────────┴──────┴─────────────┴──────────────────────┘
```

**2. app_sg - Application Server Security Group**
```
Purpose: Control traffic to application instances

Inbound Rules:
┌──────────────┬──────┬─────────────┬──────────────────────┐
│ Protocol     │ Port │ Source      │ Description          │
├──────────────┼──────┼─────────────┼──────────────────────┤
│ TCP          │ 5000 │ alb_sg      │ App traffic from ALB │
│ SSH          │ 2049 │ alb_sg      │ App traffic from ALB │  
└──────────────┴──────┴─────────────┴──────────────────────┘

Outbound Rules:
┌──────────────┬──────┬─────────────┬──────────────────────┐
│ Protocol     │ Port │ Destination │ Description          │
├──────────────┼──────┼─────────────┼──────────────────────┤
│ All          │ All  │ 0.0.0.0/0   │ All outbound         │
└──────────────┴──────┴─────────────┴──────────────────────┘
```

**3. web_sg - Bastion Host Security Group**
```
Purpose: Control traffic to bastion host

Inbound Rules:
┌──────────────┬──────┬─────────────┬──────────────────────┐
│ Protocol     │ Port │ Source      │ Description          │
├──────────────┼──────┼─────────────┼──────────────────────┤
│ SSH          │ 22   │ 0.0.0.0/0   │ SSH from anywhere    │
│ HTTP         │ 80   │ 0.0.0.0/0   │ HTTP access          │ 
└──────────────┴──────┴─────────────┴──────────────────────┘

Outbound Rules:
┌──────────────┬──────┬─────────────┬──────────────────────┐
│ Protocol     │ Port │ Destination │ Description          │
├──────────────┼──────┼─────────────┼──────────────────────┤
│ All          │ All  │ 0.0.0.0/0   │ All outbound         │
└──────────────┴──────┴─────────────┴──────────────────────┘
```

### Application Load Balancer

**ALB Configuration:**
```
Name: web-app-albb
Type: Application Load Balancer
Scheme: internet-facing
IP Address Type: IPv4
Availability Zones: ap-south-1a, ap-south-1b
Subnets: Public Subnet 1, Public Subnet 2
Security Group: alb_sg
```

**Listener Rules:**
```
Protocol: HTTP
Port: 80
Default Action: Forward to target group (app-tg)
```

**Target Group:**
```
Name: app-tg
Protocol: HTTP
Port: 5000
Target Type: instance
VPC: my vpc

Health Check Configuration:
├── Path: /
├── Protocol: HTTP
├── Port: 5000
├── Healthy Threshold: 2 consecutive checks
├── Unhealthy Threshold: 2 consecutive checks
├── Timeout: 5 seconds
├── Interval: 30 seconds
└── Success Codes: 200
```

### Auto Scaling Group

**ASG Configuration:**
```
Name: web-app_asg
Launch Template: web_app_2
Availability Zones: ap-south-1a, ap-south-1b
Subnets: Private Subnet 1, Private Subnet 2
Target Group: app-tg

Capacity:
├── Minimum: 1 instance
├── Desired: 1 instance
└── Maximum: 4 instances

Health Check:
├── Type: ELB (Load Balancer)
├── Grace Period: 300 seconds
└── Enabled: Yes
```

**Launch Template:**
```
Name: web_app_2
AMI: Custom AMI with pre-installed application
Instance Type: t3.micro
Key Pair: nn
Security Groups: app_sg
Network: Private subnets only
Public IP: Disabled

Pre-installed Components:
├── Python 3.9
├── Flask framework
├── Gunicorn WSGI server
├── Application code
├── NFS client utilities
└── Auto-mount NFS configuration
```
 

### NFS Shared Storage Architecture

**NFS Master Server:**
```
Instance Type: t3.micro
Subnet: Private Subnet 1
Security Group: Custom (allows NFS from app_sg)
Storage: 20 GB EBS volume

Exports:
/mnt/nfs_share → Mounted by all app servers

Contains:
├── SQLite database (shared.db)
├── Uploaded files
└── Application data
```

**NFS Mount on App Servers:**
```
Mount Point: /mnt/nfs_share
Mount Options: rw, sync, hard, intr
Auto-mount: Configured in /etc/fstab
Application Access: Database and file operations
```


## Deployment Steps

### Phase 1: Prerequisites Setup

**1. Install Required Tools**
```bash
# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform version

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

**2. Configure AWS Access**
```bash
aws configure
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region name: ap-south-1
# Default output format: json
```

**3. Create SSH Key Pairs**
```bash
# Bastion host key
aws ec2 create-key-pair --key-name host1 \
  --query 'KeyMaterial' --output text > host1.pem
chmod 400 host1.pem

# Application servers key
aws ec2 create-key-pair --key-name nn \
  --query 'KeyMaterial' --output text > nn.pem
chmod 400 nn.pem
```

### Phase 2: Build Custom AMI

**4. Launch Base Instance**
```bash
# Launch temporary instance for AMI creation
aws ec2 run-instances \
  --image-id ami-00ca570c1b6d79f36 \
  --instance-type t3.micro \
  --key-name nn \
  --security-group-ids sg-xxxxx \
  --subnet-id subnet-xxxxx
```

**5. Install Application Stack**
```bash
# SSH to the instance
ssh -i nn.pem ec2-user@<public-ip>

# Update system
sudo yum update -y

# Install Python 3.9
sudo yum install python3 python3-pip -y

# Install application dependencies
sudo pip3 install flask gunicorn

# Install NFS client
sudo yum install nfs-utils -y

# Create application directory
sudo mkdir -p /home/ec2-user/web_app
cd /home/ec2-user/web_app

# Deploy application code
# (Copy your Flask application files here)

# Create systemd service file
sudo nano /etc/systemd/system/webapp.service
```

**6. Configure Systemd Service**
```ini
[Unit]
Description=Flask Web Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/web_app
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**7. Enable and Test Service**
```bash
# Enable service
sudo systemctl enable webapp.service
sudo systemctl start webapp.service

# Check status
sudo systemctl status webapp.service

# Test application
curl http://localhost:5000
```

**8. Configure NFS Auto-Mount**
```bash
# Add to /etc/fstab
echo "NFS_MASTER_IP:/mnt/nfs_share /mnt/nfs_share nfs rw,sync,hard,intr 0 0" | sudo tee -a /etc/fstab

# Create mount point
sudo mkdir -p /mnt/nfs_share

# Test mount (will work after NFS server is created)
# sudo mount -a
```

**9. Create Custom AMI**
```bash
# Stop the instance
aws ec2 stop-instances --instance-ids i-xxxxx

# Create AMI
aws ec2 create-image \
  --instance-id i-xxxxx \
  --name "web-app-v1" \
  --description "Flask app with auto-scaling support"

# Note the AMI ID for Terraform configuration
```

### Phase 3: Deploy Infrastructure with Terraform

**10. Initialize Terraform**
```bash
# Create project directory
mkdir terraform-auto-scaling-app
cd terraform-auto-scaling-app

# Copy your main.tf configuration

# Initialize
terraform init
```

**11. Update Configuration**
```bash
# Edit main.tf and update:
# - AMI ID with your custom AMI
# - Key pair names
# - Any region-specific values
```

**12. Deploy Infrastructure**
```bash
# Plan deployment
terraform plan


### Phase 4: Configure NFS Server

**13. Set Up NFS Master**
```bash
# Launch NFS server instance
aws ec2 run-instances \
  --image-id ami-00ca570c1b6d79f36 \
  --instance-type t3.micro \
  --subnet-id <private-subnet-1-id> \
  --security-group-ids <nfs-security-group-id> \
  --key-name nn

# SSH via bastion
ssh -i host1.pem ec2-user@<bastion-ip>
ssh -i nn.pem ec2-user@<nfs-server-ip>

# Install NFS server
sudo yum install nfs-utils -y

# Create export directory
sudo mkdir -p /mnt/nfs_share
sudo chown ec2-user:ec2-user /mnt/nfs_share

# Configure exports
echo "/mnt/nfs_share 192.168.1.0/24(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports

# Start NFS services
sudo systemctl enable nfs-server
sudo systemctl start nfs-server
sudo exportfs -a
```

**14. Update App Servers**
```bash
# SSH to application instance
# Mount NFS share
sudo mount -t nfs <nfs-server-ip>:/mnt/nfs_share /mnt/nfs_share

# Verify mount
df -h | grep nfs_share

# Initialize database
cd /mnt/nfs_share
python3 /home/ec2-user/web_app/init_db.py
```

## Cost Breakdown

### Monthly Infrastructure Costs (ap-south-1)

**Compute Costs:**
```
Bastion Host (t3.micro):
├── Running 24/7: $0.0146/hour × 730 hours
└── Monthly Cost: $10.66

Application Instances (t3.micro):
├── Minimum (1 instance): $10.66/month
├── Average with auto scaling (1.5 instances): $16.00/month
├── Peak (4 instances): $42.64/month
└── Estimated Monthly Cost: $16-25/month

NFS Master (t3.micro):
├── Running 24/7: $0.0146/hour × 730 hours
└── Monthly Cost: $10.66
```

**Networking Costs:**
```
Application Load Balancer:
├── Fixed: $0.0306/hour × 730 hours = $22.34/month
├── LCU Charges (Light traffic): $3-5/month
└── Total: $25-27/month

NAT Gateway:
├── Fixed: $0.065/hour × 730 hours = $47.45/month
├── Data Processing: $0.065/GB
├── Typical Usage: $2-5/month
└── Total: $49-52/month

Data Transfer:
├── First 1 GB: Free
├── Next 10 TB: $0.09/GB
└── Estimated: $3-8/month
```

**Storage Costs:**
```
EBS Volumes:
├── Bastion (8 GB): $0.80/month
├── App instances (8 GB each): $0.80-3.20/month
├── NFS master (20 GB): $2.00/month
└── Total: $3.60-6.00/month

CloudWatch:
├── 10 metrics: Free tier
├── Custom metrics: ~$1/month
└── Total: $0-1/month
```

**Total Estimated Monthly Cost: $119-147/month**

### Cost Optimization Strategies


**1. Use Reserved Instances**
```
Baseline capacity: 2 instances (bastion + 1 app)
1-year commitment: Save 30-40%
3-year commitment: Save 50-60%
Savings: ~$8-12/month on baseline
```



## What I Learned

Building this auto-scaling infrastructure taught me valuable lessons about AWS architecture and production systems:


**Security Group Chaining:**
Using security group IDs as sources (instead of CIDR blocks) creates a more secure and maintainable architecture. When the ALB security group is used as the source for the app tier, it automatically includes all ALB instances without manual IP management.

**Multi-AZ is Essential:**
Deploying across ap-south-1a and ap-south-1b means a datacenter failure doesn't take down the application. The ALB automatically routes traffic only to healthy instances in functioning AZs.

**Health Checks Save Applications:**
ELB health checks automatically detect failed instances and stop sending them traffic. Combined with Auto Scaling, unhealthy instances are automatically terminated and replaced.

**Shared Storage Challenges:**
NFS provides shared storage but has limitations:
- File-based locking issues with SQLite
- Single point of failure if not properly designed
- Network performance overhead
- Better solution: Managed services like RDS and EFS

## Future Improvements

### Immediate (Fix Single Points of Failure)

1. Replace SQLite + NFS with Amazon RDS

**Current Problem:**
The application currently uses SQLite database stored on an NFS share. This creates serious issues when multiple application servers try to write to the same database file simultaneously, leading to database locks and potential data corruption.

**Proposed Solution:**
Implement Amazon RDS (Relational Database Service) with MySQL or PostgreSQL engine. This provides a managed database service specifically designed for multi-server applications.

2. Add HTTPS Support with SSL/TLS

**Current Situation:**
The application currently serves traffic over HTTP (port 80) only, which means all data is transmitted in plain text and can be intercepted.

**Proposed Enhancement:**
Enable HTTPS on the Application Load Balancer using AWS Certificate Manager for SSL/TLS certificates.


3. Automated Backup Strategy

**Current Situation:**
No systematic backup process. If instances fail or data is corrupted, recovery depends on manual efforts and recent AMIs.

**Proposed Solution:**
Implement automated backup strategy using AWS Data Lifecycle Manager for EBS snapshots.


4. IF Needed Multi-Region Deployment for Global Users

**Current Limitation:**
Application runs only in ap-south-1 (Mumbai). Users in other regions experience higher latency, and a regional AWS outage would take down the entire application.

**Proposed Enhancement:**
Deploy identical infrastructure in a second region (e.g., us-east-1 for North American users) with Route53 for intelligent traffic routing.





## Contact

- Email: rahulbaswala73@gmail.com
- LinkedIn: [your-profile](https://linkedin.com/in/your-profile)
- GitHub: [Wolfking92](https://github.com/your-username)






