# Security Policy

## Supported Versions

We maintain security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Security Dependencies

We maintain strict version requirements for security-critical dependencies:

- PyPDF2 >= 3.0.2 (fixes CVE-2023-36464)
- Werkzeug >= 3.0.1
- cryptography >= 41.0.0
- certifi >= 2023.7.22

## Security Features

1. **Network Security**:
   - Default to localhost binding
   - Explicit configuration required for external access
   - CORS and security headers enabled

2. **File Security**:
   - Secure file handling
   - Automatic cleanup of uploaded files
   - File type validation
   - Size limits enforced

3. **API Security**:
   - Rate limiting enabled
   - Input validation
   - Error handling
   - Secure defaults

4. **Development Security**:
   - Debug mode restricted to localhost
   - Security-focused configuration
   - Regular dependency updates

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **Do Not** create a public GitHub issue
2. Email security@your-domain.com with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work on:
1. Confirming the vulnerability
2. Patching the issue
3. Releasing a security update
4. Publicly disclosing the issue (after patch)

## Security Best Practices

When deploying this application:

1. **Environment**:
   - Use HTTPS in production
   - Set secure environment variables
   - Monitor system resources
   - Keep dependencies updated

2. **Configuration**:
   - Review security settings
   - Use secure defaults
   - Enable logging
   - Set appropriate file permissions

3. **Monitoring**:
   - Monitor access logs
   - Track resource usage
   - Set up alerts
   - Regular security scans