#!/usr/bin/env python3
"""
Enhanced Security Pipeline Configuration Generator using Claude Sonnet
This script uses AI to generate dynamic pipeline configurations based on code analysis
"""

import json
import os
import yaml
from typing import Dict, List, Any
import anthropic
from datetime import datetime

class SecurityPipelineGenerator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze the codebase to understand security requirements"""
        analysis = {
            'languages': [],
            'frameworks': [],
            'dependencies': [],
            'security_features': [],
            'risk_level': 'medium'
        }
        
        # Analyze Python files
        python_files = []
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        if python_files:
            analysis['languages'].append('python')
            
        # Analyze requirements.txt
        requirements_path = os.path.join(self.project_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            with open(requirements_path, 'r') as f:
                requirements = f.read()
                analysis['dependencies'] = [line.split('>=')[0].split('==')[0] 
                                          for line in requirements.split('\n') 
                                          if line and not line.startswith('#')]
        
        # Detect frameworks
        if 'fastapi' in analysis['dependencies']:
            analysis['frameworks'].append('fastapi')
        if 'django' in analysis['dependencies']:
            analysis['frameworks'].append('django')
        if 'flask' in analysis['dependencies']:
            analysis['frameworks'].append('flask')
            
        # Detect security features
        security_deps = ['bcrypt', 'python-jose', 'passlib', 'oauth2', 'jwt']
        analysis['security_features'] = [dep for dep in security_deps 
                                       if any(dep in req for req in analysis['dependencies'])]
        
        return analysis

    def generate_security_config(self, analysis: Dict[str, Any]) -> str:
        """Generate security configuration using Claude Sonnet"""
        
        prompt = f"""
        As a DevSecOps expert, generate a comprehensive security configuration for a CI/CD pipeline based on the following codebase analysis:

        Project Analysis:
        - Languages: {analysis['languages']}
        - Frameworks: {analysis['frameworks']}
        - Dependencies: {analysis['dependencies'][:20]}  # First 20 deps
        - Security Features: {analysis['security_features']}
        - Risk Level: {analysis['risk_level']}

        Please generate:
        1. SAST (Static Application Security Testing) configuration
        2. DAST (Dynamic Application Security Testing) settings
        3. Container security scanning parameters
        4. Dependency vulnerability scanning rules
        5. Security gates and thresholds
        6. Compliance checklist (OWASP Top 10, GDPR)

        Format the response as YAML configuration that can be used in GitHub Actions.
        Include specific tool configurations for:
        - Bandit (Python SAST)
        - Safety (Python dependency check)
        - Semgrep (Multi-language SAST)
        - OWASP ZAP (DAST)
        - Trivy (Container scanning)
        - ESLint Security Plugin (JavaScript)

        Make the configuration production-ready with appropriate thresholds and security gates.
        """

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return response.content[0].text

    def generate_pipeline_stages(self, analysis: Dict[str, Any]) -> str:
        """Generate optimized pipeline stages based on project characteristics"""
        
        prompt = f"""
        As a CI/CD pipeline expert, design optimized pipeline stages for a Python web application with the following characteristics:

        Analysis:
        - Languages: {analysis['languages']}
        - Frameworks: {analysis['frameworks']}
        - Dependencies: {len(analysis['dependencies'])} total dependencies
        - Security Features: {analysis['security_features']}

        Design pipeline stages that include:
        1. Parallel execution where possible
        2. Fail-fast mechanisms
        3. Caching strategies
        4. Security gates at appropriate points
        5. Deployment strategies (blue-green, canary)
        6. Rollback mechanisms
        7. Monitoring and alerting integration

        Consider the project uses:
        - FastAPI framework
        - Redis caching
        - PostgreSQL database
        - Docker containerization
        - Kubernetes deployment
        - Prometheus monitoring

        Generate a GitHub Actions workflow that is:
        - Production-ready
        - Secure by default
        - Optimized for performance
        - Includes comprehensive error handling
        - Has proper artifact management
        - Includes audit logging

        Format as GitHub Actions YAML.
        """

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return response.content[0].text

    def generate_compliance_report(self, scan_results: Dict[str, Any]) -> str:
        """Generate compliance report based on scan results"""
        
        prompt = f"""
        As a compliance expert, analyze the following security scan results and generate a comprehensive compliance report:

        Scan Results Summary:
        {json.dumps(scan_results, indent=2)}

        Generate a compliance report that covers:
        1. OWASP Top 10 2021 compliance status
        2. GDPR compliance assessment
        3. Security control effectiveness
        4. Risk assessment and mitigation recommendations
        5. Audit trail summary
        6. Remediation priorities
        7. Executive summary

        The report should be:
        - Professional and audit-ready
        - Include specific findings and evidence
        - Provide actionable recommendations
        - Include compliance scores/ratings
        - Reference relevant standards and frameworks

        Format as structured markdown with sections for each compliance area.
        """

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return response.content[0].text

    def interpret_security_logs(self, log_content: str) -> str:
        """Interpret security scan logs and provide actionable insights"""
        
        prompt = f"""
        As a security expert, analyze the following security scan logs and provide actionable insights:

        Security Scan Logs:
        {log_content[:3000]}  # Limit log content

        Please provide:
        1. Summary of security findings
        2. Critical vulnerabilities that need immediate attention
        3. False positive identification
        4. Risk prioritization
        5. Specific remediation steps
        6. Code examples for fixes where applicable
        7. Preventive measures for the future

        Format the response as structured analysis with:
        - Executive summary
        - Detailed findings
        - Risk assessment
        - Remediation recommendations
        - Prevention strategies
        """

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return response.content[0].text

    def generate_runbook(self, pipeline_config: Dict[str, Any]) -> str:
        """Generate operational runbook for the security pipeline"""
        
        prompt = f"""
        As a DevOps expert, create a comprehensive operational runbook for managing a security CI/CD pipeline with the following configuration:

        Pipeline Configuration:
        {json.dumps(pipeline_config, indent=2)[:2000]}

        The runbook should include:
        1. Pipeline overview and architecture
        2. Operational procedures
        3. Troubleshooting guides
        4. Security incident response procedures
        5. Monitoring and alerting setup
        6. Maintenance tasks and schedules
        7. Emergency procedures
        8. Contact information and escalation paths
        9. Performance tuning guidelines
        10. Disaster recovery procedures

        Format as a professional operations manual with:
        - Clear step-by-step procedures
        - Decision trees for troubleshooting
        - Commands and scripts examples
        - Monitoring dashboards and alerts
        - SLA definitions
        """

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return response.content[0].text

    def save_generated_configs(self, configs: Dict[str, str]):
        """Save all generated configurations to files"""
        
        config_dir = os.path.join(self.project_path, 'cicd-configs')
        os.makedirs(config_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for config_name, content in configs.items():
            filename = f"{config_name}_{timestamp}.yml" if config_name.endswith('config') else f"{config_name}_{timestamp}.md"
            filepath = os.path.join(config_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            print(f"Generated {config_name}: {filepath}")

def main():
    """Main execution function"""
    
    # Get API key from environment
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    generator = SecurityPipelineGenerator(api_key)
    
    print("🔍 Analyzing codebase...")
    analysis = generator.analyze_codebase()
    print(f"✅ Analysis complete: {len(analysis['dependencies'])} dependencies found")
    
    print("🔒 Generating security configuration...")
    security_config = generator.generate_security_config(analysis)
    
    print("🚀 Generating pipeline stages...")
    pipeline_stages = generator.generate_pipeline_stages(analysis)
    
    print("📋 Generating compliance template...")
    compliance_template = generator.generate_compliance_report({
        'analysis': analysis,
        'timestamp': datetime.now().isoformat(),
        'status': 'template'
    })
    
    print("📖 Generating operational runbook...")
    runbook = generator.generate_runbook({
        'project_analysis': analysis,
        'security_tools': ['bandit', 'safety', 'semgrep', 'zap', 'trivy'],
        'deployment_targets': ['staging', 'production']
    })
    
    # Save all configurations
    configs = {
        'security_config': security_config,
        'pipeline_stages': pipeline_stages,
        'compliance_template': compliance_template,
        'operational_runbook': runbook
    }
    
    print("💾 Saving generated configurations...")
    generator.save_generated_configs(configs)
    
    print("✅ Security pipeline configuration generation complete!")
    print("📁 Check the cicd-configs directory for generated files")

if __name__ == "__main__":
    main()
