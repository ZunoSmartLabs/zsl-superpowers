---
name: steampipe
description: Use when querying AWS infrastructure via Steampipe. Provides correct table names, column schemas, and query patterns.
user-invocable: false
---

# Steampipe AWS Query Reference

When querying AWS infrastructure, use `steampipe query "SQL"` via Bash. Steampipe uses PostgreSQL-compatible SQL against the `aws` schema.

## Multi-account setups

If `~/.steampipe/config/aws.spc` defines an aggregator connection named `aws` over per-account connections (e.g. `aws_test`, `aws_prod`, `aws_mgmt`), unqualified queries fan out across all accounts in parallel:

```sql
-- Hits every account; account_id tells you which row came from where
SELECT account_id, instance_id, tags ->> 'Name' AS name
FROM aws_ec2_instance
ORDER BY account_id;
```

To target a single account, prefix the table with the connection name:

```sql
SELECT instance_id FROM aws_prod.aws_ec2_instance;
```

Use `select distinct account_id from aws_account` to confirm which accounts the aggregator is reaching before relying on a fan-out result. If only one `account_id` comes back, the unqualified query is hitting a single connection — check for an aggregator named `aws` in `aws.spc`.

## Key Rules

- All tables are in the `aws` schema (referenced without schema prefix in queries)
- JSONB columns use `->` (object) and `->>` (text) operators for access
- Tags are typically stored as `tags` (jsonb map) — filter with `tags ->> 'Name' = 'value'`
- Every table has: `title`, `tags`, `akas`, `partition`, `region`, `account_id`, `sp_connection_name`
- Use `information_schema.columns` to discover columns for tables not listed below

## Common Tables and Key Columns

### Compute

**aws_ec2_instance**
`instance_id`, `instance_type`, `instance_state`, `private_ip_address` (inet), `public_ip_address` (inet), `private_dns_name`, `public_dns_name`, `vpc_id`, `subnet_id`, `key_name`, `image_id`, `launch_time`, `platform`, `architecture`, `security_groups` (jsonb), `network_interfaces` (jsonb), `iam_instance_profile_arn`, `metadata_options` (jsonb), `tags` (jsonb)

**aws_lambda_function**
`name`, `arn`, `runtime`, `handler`, `memory_size`, `timeout`, `state`, `role`, `vpc_id`, `code_size`, `description`, `last_modified`, `environment_variables` (jsonb), `url_config` (jsonb), `layers` (jsonb), `tags` (jsonb)

### Containers

**aws_ecs_cluster**
`cluster_name`, `cluster_arn`, `status`, `active_services_count`, `running_tasks_count`, `registered_container_instances_count`, `capacity_providers` (jsonb), `settings` (jsonb), `tags` (jsonb)

**aws_ecs_service**
`service_name`, `arn`, `status`, `cluster_arn`, `task_definition`, `desired_count`, `running_count`, `launch_type`, `deployment_controller_type`, `network_configuration` (jsonb), `load_balancers` (jsonb), `deployments` (jsonb), `tags` (jsonb)

**aws_ecs_task**
`task_arn`, `cluster_name`, `cluster_arn`, `desired_status`, `last_status`, `launch_type`, `cpu` (bigint), `memory` (bigint), `service_name`, `task_definition_arn`, `containers` (jsonb), `tags` (jsonb)

**aws_ecs_task_definition**
`task_definition_arn`, `family`, `revision`, `status`, `cpu` (bigint), `memory` (bigint), `network_mode`, `execution_role_arn`, `task_role_arn`, `container_definitions` (jsonb), `volumes` (jsonb), `tags` (jsonb)

### Load Balancing

**aws_ec2_application_load_balancer**
`name`, `arn`, `dns_name`, `canonical_hosted_zone_id`, `scheme`, `type`, `vpc_id`, `state_code`, `ip_address_type`, `security_groups` (jsonb), `availability_zones` (jsonb), `tags` (jsonb)

Note: The hosted zone column is `canonical_hosted_zone_id`, NOT `zone_id`.

Note: There is NO generic `aws_ec2_load_balancer` table. Use specific types:
- `aws_ec2_application_load_balancer` (ALB)
- `aws_ec2_network_load_balancer` (NLB)
- `aws_ec2_gateway_load_balancer` (GLB)
- `aws_ec2_classic_load_balancer` (CLB)

**aws_ec2_load_balancer_listener**
`arn`, `load_balancer_arn`, `port`, `protocol`, `ssl_policy`, `default_actions` (jsonb), `certificates` (jsonb)

**aws_ec2_load_balancer_listener_rule**
Table exists for listener rules.

**aws_ec2_target_group**
`target_group_name`, `target_group_arn`, `target_type`, `port`, `protocol`, `vpc_id`, `health_check_path`, `health_check_port`, `health_check_protocol`, `healthy_threshold_count`, `load_balancer_arns` (jsonb), `target_health_descriptions` (jsonb), `tags` (jsonb)

### Networking

**aws_vpc**
Standard VPC fields.

**aws_vpc_security_group**
`group_name`, `group_id`, `arn`, `description`, `vpc_id`, `owner_id`, `ip_permissions` (jsonb), `ip_permissions_egress` (jsonb), `tags` (jsonb)

**aws_vpc_subnet**
Standard subnet fields.

### Identity & Auth

**aws_cognito_user_pool**
`id`, `name`, `arn`, `domain`, `custom_domain`, `status`, `mfa_configuration`, `estimated_number_of_users`, `deletion_protection`, `admin_create_user_config` (jsonb), `schema_attributes` (jsonb), `policies` (jsonb), `tags` (jsonb)

Note: Column is `domain` not `hosted_domain`. Column is `id` not `pool_id`.

**aws_cognito_identity_pool**
Separate table for identity pools (federated identities).

**aws_cognito_identity_provider**
Identity providers attached to user pools.

**aws_cognito_user_group**
Groups within user pools.

### Storage

**aws_s3_bucket**
`name`, `arn`, `creation_date`, `versioning_enabled`, `bucket_policy_is_public`, `block_public_acls`, `block_public_policy`, `server_side_encryption_configuration` (jsonb), `lifecycle_rules` (jsonb), `logging` (jsonb), `tags` (jsonb)

**aws_dynamodb_table**
`name`, `arn`, `table_id`, `table_status`, `table_class`, `billing_mode`, `item_count`, `table_size_bytes`, `read_capacity`, `write_capacity`, `key_schema` (jsonb), `attribute_definitions` (jsonb), `tags` (jsonb)

### Deployment

**aws_codedeploy_app**
`application_name`, `application_id`, `arn`, `compute_platform`, `create_time`, `linked_to_github`, `tags` (jsonb)

**aws_codedeploy_deployment_group**
Deployment groups within CodeDeploy apps.

**aws_codedeploy_deployment_config**
Deployment configurations.

### Infrastructure as Code

**aws_cloudformation_stack**
`id`, `name`, `arn`, `status`, `stack_status_reason`, `description`, `creation_time`, `last_updated_time`, `outputs` (jsonb), `parameters` (jsonb), `resources` (jsonb), `template_body`, `tags` (jsonb)

### SSM

**aws_ssm_managed_instance**
`instance_id`, `name`, `arn`, `ping_status`, `agent_version`, `platform_name`, `platform_type`, `platform_version`, `ip_address` (inet), `computer_name`, `association_status`, `last_ping_date_time`, `registration_date`

### IAM

**aws_iam_role** — IAM roles
**aws_iam_policy** — IAM policies
**aws_iam_user** — IAM users
**aws_iam_instance_profile** — Instance profiles

### Monitoring

**aws_cloudwatch_log_group** — CloudWatch log groups
**aws_cloudwatch_alarm** — CloudWatch alarms

### DNS

**aws_route53_zone** — Hosted zones
**aws_route53_record** — DNS records

### Secrets

**aws_secretsmanager_secret** — Secrets Manager secrets

## Common Query Patterns

```sql
-- Find EC2 instances by tag
SELECT instance_id, instance_state, tags ->> 'Name' as name
FROM aws_ec2_instance
WHERE tags ->> 'Name' ILIKE '%portal%';

-- Security group rules for an instance
SELECT sg.group_name, sg.ip_permissions
FROM aws_vpc_security_group sg
WHERE sg.group_id IN (
  SELECT jsonb_array_elements(security_groups) ->> 'GroupId'
  FROM aws_ec2_instance
  WHERE instance_id = 'i-xxx'
);

-- ALB with listeners
SELECT alb.name, alb.dns_name, l.port, l.protocol
FROM aws_ec2_application_load_balancer alb
JOIN aws_ec2_load_balancer_listener l ON l.load_balancer_arn = alb.arn;

-- Cognito user pools
SELECT name, id, domain, mfa_configuration, estimated_number_of_users
FROM aws_cognito_user_pool;

-- CloudFormation stack outputs
SELECT name, status, outputs
FROM aws_cloudformation_stack
WHERE name ILIKE '%portal%';

-- Discover columns for any table
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'aws' AND table_name = 'TABLE_NAME'
ORDER BY ordinal_position;
```
