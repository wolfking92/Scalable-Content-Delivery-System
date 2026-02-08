resource "aws_s3_bucket" "web-app-27-01-2026" {
    bucket = "web-app-27-01-2026"
    region = "ap-south-1"
    tags = {
        Name = "Bucket from Terraform"
    }
}

resource "aws_s3_bucket_public_access_block" "block_public" {
    bucket = aws_s3_bucket.web-app-27-01-2026.id

    block_public_acls   = false
    block_public_policy = false
    ignore_public_acls  = false
    restrict_public_buckets = false
}

resource "aws_s3_bucket_versioning" "versioning1" {
    bucket = aws_s3_bucket.web-app-27-01-2026.id
    versioning_configuration {
        status = "Enabled"
    }
}






