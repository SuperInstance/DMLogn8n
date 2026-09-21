# DMLog Infrastructure Security Hardening

This directory contains comprehensive security configurations for the DMLog infrastructure, implementing defense-in-depth security architecture across all layers.

## Security Architecture Overview

The security implementation follows the **Defense-in-Depth** principle with multiple layers of protection:

### 1. Kubernetes Security
- **Pod Security Standards** (replacing deprecated PSPs)
- **Network Policies** with zero-trust networking
- **RBAC** with principle of least privilege
- **Service Accounts** with minimal permissions
- **Security Contexts** for non-root execution

### 2. Container Security
- **Image Scanning** with Trivy and Grype
- **Runtime Security** with Falco
- **Admission Controllers** with OPA Gatekeeper
- **Secure Base Images** with minimal attack surface
- **Seccomp Profiles** for system call filtering

### 3. Network Security
- **VPC Security Groups** with restrictive rules
- **Network ACLs** for subnet-level protection
- **VPC Endpoints** for private connectivity
- **WAF** with comprehensive rule sets
- **DDoS Protection** with AWS Shield

### 4. Application Security
- **External Secrets Management** with AWS Secrets Manager
- **Secret Rotation** with Lambda functions
- **Encryption at Rest** with KMS
- **Certificate Management** with ACM

### 5. Monitoring & Compliance
- **Security Hub** for centralized security monitoring
- **GuardDuty** for threat detection
- **Config Rules** for compliance checking
- **Inspector2** for vulnerability scanning
- **Automated Security Scanning** with scheduled checks

## Directory Structure

```
security/
├── kubernetes/                    # Kubernetes security configurations
│   ├── pod-security-standards.yaml    # Pod Security Standards
│   ├── security-contexts.yaml         # Security contexts and profiles
│   ├── network-policies.yaml          # Network policies
│   └── rbac-service-accounts.yaml    # RBAC and service accounts
├── container-security/            # Container security
│   ├── image-scanning.yaml             # Image scanning configurations
│   └── secure-base-images.yaml        # Secure base images
├── terraform/                      # Infrastructure security
│   ├── vpc-security.tf                # VPC and network security
│   └── vpc-security-variables.tf      # VPC security variables
├── network-security/              # Network and edge security
│   ├── waf-ddos-protection.tf         # WAF and DDoS protection
│   ├── waf-ddos-variables.tf          # WAF/DDoS variables
│   └── cloudfront-function.js         # CloudFront security headers
├── secrets-management/            # Secrets management
│   ├── external-secrets.tf            # AWS Secrets Manager setup
│   ├── lambda/                        # Lambda rotation functions
│   ├── external-secrets-examples.yaml # External Secrets examples
│   └── secrets-variables.tf           # Secrets management variables
├── automation/                     # Security automation
│   ├── security-automation.tf         # Security automation infrastructure
│   ├── lambda/                        # Security automation Lambda
│   └── automation-variables.tf        # Automation variables
├── policies/                       # Security policies and procedures
└── README.md                      # This file
```

## Key Security Features

### 🔒 Kubernetes Security

#### Pod Security Standards
- **Restricted Profile**: Maximum security for production workloads
- **Baseline Profile**: Good security for development/staging
- **Privileged Profile**: Limited access for system components

#### Network Policies
- **Zero-Trust Architecture**: Default deny all traffic
- **Microsegmentation**: Granular traffic control between components
- **Service Mesh Integration**: Istio policies for advanced security

#### RBAC Configuration
- **Least Privilege**: Minimal permissions per component
- **Service Account Isolation**: Separate accounts per workload
- **Regular Auditing**: Automated permission reviews

### 🛡️ Container Security

#### Image Security
- **Multi-Stage Builds**: Minimal production images
- **Vulnerability Scanning**: Automated detection with Trivy/Grype
- **Base Image Hardening**: Minimal packages, non-root users
- **Runtime Monitoring**: Falco for behavioral analysis

#### Admission Control
- **OPA Gatekeeper**: Policy-as-code enforcement
- **Image Verification**: Digital signature validation
- **Resource Limits**: CPU/memory restrictions
- **Security Context Validation**: Enforce secure configurations

### 🌐 Network Security

#### VPC Security
- **Private Subnets**: Isolated application infrastructure
- **Security Groups**: Stateful filtering at instance level
- **Network ACLs**: Stateless subnet-level protection
- **VPC Endpoints**: Private connectivity to AWS services

#### Edge Protection
- **AWS WAF**: Comprehensive web application firewall
- **DDoS Protection**: AWS Shield Advanced for mitigation
- **CloudFront**: CDN with security headers and DDoS protection
- **Certificate Management**: Automated SSL/TLS with ACM

### 🔐 Secrets Management

#### AWS Secrets Manager
- **Centralized Storage**: Encrypted secret storage
- **Automatic Rotation**: Lambda-based rotation with 30-day cycles
- **External Secrets Operator**: Kubernetes integration
- **Audit Logging**: Complete access audit trail

#### Encryption
- **KMS Keys**: Customer-managed encryption keys
- **Envelope Encryption**: Efficient key management
- **Key Rotation**: Automatic key rotation policies
- **Access Control**: Fine-grained key permissions

### 🔍 Security Monitoring

#### Threat Detection
- **AWS GuardDuty**: Intelligent threat detection
- **Security Hub**: Centralized security findings
- **Inspector2**: Automated vulnerability scanning
- **CloudTrail**: Complete API audit trail

#### Compliance Monitoring
- **AWS Config**: Continuous compliance checking
- **CIS Controls**: Industry-standard security controls
- **Custom Rules**: Organization-specific requirements
- **Automated Remediation**: Self-healing security configurations

## Implementation Guidelines

### 1. Prerequisites

Ensure you have the following permissions:
- AWS IAM permissions for security services
- Kubernetes cluster admin access
- Terraform CLI installed
- kubectl configured for cluster access

### 2. Deployment Steps

#### Phase 1: Foundation Security
```bash
# Deploy VPC and network security
cd terraform/
terraform init
terraform apply

# Deploy secrets management infrastructure
cd ../secrets-management/
terraform init
terraform apply
```

#### Phase 2: Container Security
```bash
# Deploy External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets --create-namespace

# Deploy security scanning tools
kubectl apply -f ../container-security/
```

#### Phase 3: Kubernetes Security
```bash
# Deploy Pod Security Standards and RBAC
kubectl apply -f ../kubernetes/

# Deploy network policies
kubectl apply -f ../kubernetes/network-policies.yaml
```

#### Phase 4: Monitoring & Automation
```bash
# Deploy security automation
cd ../automation/
terraform init
terraform apply
```

### 3. Configuration Requirements

#### Environment Variables
```bash
export TF_VAR_project_name="dmlog"
export TF_VAR_environment="production"
export TF_VAR_aws_region="us-west-2"
export TF_VAR_slack_webhook_url="https://hooks.slack.com/..."
```

#### Required Secrets
- Database credentials (auto-generated)
- Redis passwords (auto-generated)
- JWT secret keys (auto-generated)
- API keys for external services
- SSL certificates (managed by ACM)

### 4. Security Validation

#### Automated Checks
```bash
# Run security compliance scan
aws securityhub get-findings --filters 'Field=SeverityText,Value=HIGH'

# Check vulnerability scan results
aws inspector2 list-findings

# Validate network policies
kubectl get networkpolicies --all-namespaces

# Verify pod security compliance
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext}{"\n"}{end}'
```

#### Manual Validation
1. **Network Connectivity**: Test that only allowed traffic flows
2. **Secrets Access**: Verify secrets are properly encrypted and accessible
3. **Image Security**: Confirm all images are scanned and compliant
4. **RBAC Permissions**: Validate least privilege access
5. **Monitoring Alerts**: Test security alert notifications

## Security Best Practices

### 1. Regular Maintenance
- **Weekly**: Review security findings and remediation
- **Monthly**: Update security policies and rules
- **Quarterly**: Security assessments and penetration testing
- **Annually**: Complete security architecture review

### 2. Incident Response
- **Detection**: Automated monitoring and alerting
- **Analysis**: Security team investigation procedures
- **Containment**: Automated and manual containment steps
- **Recovery**: System restoration and post-incident analysis

### 3. Compliance Requirements
- **SOC 2**: Security and availability controls
- **PCI DSS**: Payment card industry standards (if applicable)
- **HIPAA**: Healthcare information protection (if applicable)
- **GDPR**: Data protection and privacy controls

### 4. Access Management
- **MFA Required**: Multi-factor authentication for all access
- **Just-in-Time Access**: Temporary elevated permissions
- **Access Reviews**: Quarterly permission audits
- **Session Logging**: Complete session activity tracking

## Troubleshooting

### Common Issues

#### Pod Security Standards Violations
```bash
# Check pod security violations
kubectl get pods -A | grep Error
kubectl describe pod <pod-name> -n <namespace>

# Fix security context violations
kubectl edit deployment <deployment-name> -n <namespace>
```

#### Network Policy Issues
```bash
# Check network policy enforcement
kubectl get networkpolicy -A
kubectl describe networkpolicy <policy-name> -n <namespace>

# Debug network connectivity
kubectl exec -it <pod-name> -n <namespace> -- nslookup <service-name>
```

#### Secrets Access Issues
```bash
# Check external secrets sync
kubectl get externalsecret -A
kubectl describe externalsecret <secret-name> -n <namespace>

# Verify secret store connection
kubectl get secretstore -A
kubectl describe secretstore <store-name> -n <namespace>
```

#### Security Scanning Failures
```bash
# Check Lambda function logs
aws logs tail /aws/lambda/<function-name> --follow

# Verify security automation permissions
aws iam simulate-principal-policy --policy-source-arn <role-arn> \
  --action-names secretsmanager:GetSecretValue --resource-arns <secret-arn>
```

## Support and Escalation

### Security Team Contacts
- **Security Lead**: security-team@company.com
- **Incident Response**: incident@company.com
- **Compliance**: compliance@company.com

### Emergency Procedures
1. **Critical Security Event**: Call security hotline immediately
2. **Data Breach**: Follow incident response playbook
3. **Service Outage**: Contact on-call engineering team
4. **Compliance Issue**: Notify compliance team immediately

### Documentation and Resources
- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)
- [Kubernetes Security Guidelines](https://kubernetes.io/docs/concepts/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Controls](https://www.cisecurity.org/controls/)

## Version History

- **v1.0.0**: Initial security implementation
- **v1.1.0**: Added external secrets management
- **v1.2.0**: Enhanced WAF and DDoS protection
- **v1.3.0**: Comprehensive security automation
- **v2.0.0**: Complete security hardening with all layers

---

**Security is everyone's responsibility. Follow these guidelines and report any security concerns immediately.**