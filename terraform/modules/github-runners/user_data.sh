#!/bin/bash

# GitHub Actions Runner Setup with CIS Hardening
# This script configures Ubuntu instances as GitHub Actions self-hosted runners
# with CIS Level 1 security hardening

set -euo pipefail

# Variables from Terraform
GITHUB_TOKEN="${github_token}"
GITHUB_ORG="${github_organization}"
GITHUB_REPO="${github_repository}"
RUNNER_NAME_PREFIX="${runner_name_prefix}"
AWS_REGION="${region}"
ENABLE_CIS_HARDENING="${enable_cis_hardening}"
CLOUDWATCH_LOG_GROUP="${cloudwatch_log_group}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a /var/log/runner-setup.log
}

log "Starting GitHub Runner setup with CIS hardening"

# Update system
log "Updating system packages"
apt-get update
apt-get upgrade -y

# Install essential packages
log "Installing essential packages"
apt-get install -y \
    curl \
    wget \
    unzip \
    jq \
    docker.io \
    docker-compose \
    awscli \
    fail2ban \
    ufw \
    aide \
    rkhunter \
    chkrootkit \
    auditd \
    rsyslog \
    logrotate \
    ntp

# CIS Hardening if enabled
if [ "$ENABLE_CIS_HARDENING" = "true" ]; then
    log "Applying CIS Level 1 hardening"
    
    # 1.1.1.1 Ensure mounting of cramfs filesystems is disabled
    echo "install cramfs /bin/true" >> /etc/modprobe.d/CIS.conf
    
    # 1.1.1.2 Ensure mounting of freevxfs filesystems is disabled
    echo "install freevxfs /bin/true" >> /etc/modprobe.d/CIS.conf
    
    # 1.1.1.3 Ensure mounting of jffs2 filesystems is disabled
    echo "install jffs2 /bin/true" >> /etc/modprobe.d/CIS.conf
    
    # 1.1.1.4 Ensure mounting of hfs filesystems is disabled
    echo "install hfs /bin/true" >> /etc/modprobe.d/CIS.conf
    
    # 1.1.1.5 Ensure mounting of hfsplus filesystems is disabled
    echo "install hfsplus /bin/true" >> /etc/modprobe.d/CIS.conf
    
    # 1.1.1.6 Ensure mounting of squashfs filesystems is disabled
    echo "install squashfs /bin/true" >> /etc/modprobe.d/CIS.conf
    
    # 1.1.1.7 Ensure mounting of udf filesystems is disabled
    echo "install udf /bin/true" >> /etc/modprobe.d/CIS.conf
    
    # 1.1.23 Disable USB Storage
    echo "install usb-storage /bin/true" >> /etc/modprobe.d/CIS.conf
    
    # 1.4.1 Ensure permissions on bootloader config are configured
    chown root:root /boot/grub/grub.cfg 2>/dev/null || true
    chmod og-rwx /boot/grub/grub.cfg 2>/dev/null || true
    
    # 1.5.1 Ensure core dumps are restricted
    echo "* hard core 0" >> /etc/security/limits.conf
    echo "fs.suid_dumpable = 0" >> /etc/sysctl.conf
    
    # 1.5.3 Ensure address space layout randomization (ASLR) is enabled
    echo "kernel.randomize_va_space = 2" >> /etc/sysctl.conf
    
    # 3.1.1 Ensure IP forwarding is disabled
    echo "net.ipv4.ip_forward = 0" >> /etc/sysctl.conf
    echo "net.ipv6.conf.all.forwarding = 0" >> /etc/sysctl.conf
    
    # 3.1.2 Ensure packet redirect sending is disabled
    echo "net.ipv4.conf.all.send_redirects = 0" >> /etc/sysctl.conf
    echo "net.ipv4.conf.default.send_redirects = 0" >> /etc/sysctl.conf
    
    # 3.2.1 Ensure source routed packets are not accepted
    echo "net.ipv4.conf.all.accept_source_route = 0" >> /etc/sysctl.conf
    echo "net.ipv4.conf.default.accept_source_route = 0" >> /etc/sysctl.conf
    echo "net.ipv6.conf.all.accept_source_route = 0" >> /etc/sysctl.conf
    echo "net.ipv6.conf.default.accept_source_route = 0" >> /etc/sysctl.conf
    
    # 3.2.2 Ensure ICMP redirects are not accepted
    echo "net.ipv4.conf.all.accept_redirects = 0" >> /etc/sysctl.conf
    echo "net.ipv4.conf.default.accept_redirects = 0" >> /etc/sysctl.conf
    echo "net.ipv6.conf.all.accept_redirects = 0" >> /etc/sysctl.conf
    echo "net.ipv6.conf.default.accept_redirects = 0" >> /etc/sysctl.conf
    
    # 3.2.3 Ensure secure ICMP redirects are not accepted
    echo "net.ipv4.conf.all.secure_redirects = 0" >> /etc/sysctl.conf
    echo "net.ipv4.conf.default.secure_redirects = 0" >> /etc/sysctl.conf
    
    # 3.2.4 Ensure suspicious packets are logged
    echo "net.ipv4.conf.all.log_martians = 1" >> /etc/sysctl.conf
    echo "net.ipv4.conf.default.log_martians = 1" >> /etc/sysctl.conf
    
    # Apply sysctl settings
    sysctl -p
    
    log "CIS hardening applied"
fi

# Configure UFW firewall
log "Configuring UFW firewall"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow out 443/tcp
ufw allow out 80/tcp
ufw allow out 53
ufw allow out 123/udp
ufw --force enable

# Configure Fail2Ban
log "Configuring Fail2Ban"
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Configure audit daemon
log "Configuring audit daemon"
cat > /etc/audit/rules.d/CIS.rules << EOF
# CIS Audit Rules
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k logins
-w /var/log/btmp -p wa -k logins
-w /etc/sudoers -p wa -k scope
-w /etc/sudoers.d/ -p wa -k scope
EOF

systemctl enable auditd
systemctl start auditd

# Install CloudWatch agent
log "Installing CloudWatch agent"
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/runner-setup.log",
                        "log_group_name": "$CLOUDWATCH_LOG_GROUP",
                        "log_stream_name": "{instance_id}/runner-setup"
                    },
                    {
                        "file_path": "/var/log/syslog",
                        "log_group_name": "$CLOUDWATCH_LOG_GROUP",
                        "log_stream_name": "{instance_id}/syslog"
                    },
                    {
                        "file_path": "/var/log/auth.log",
                        "log_group_name": "$CLOUDWATCH_LOG_GROUP",
                        "log_stream_name": "{instance_id}/auth"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "CWAgent",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
    -s

# Create runner user
log "Creating runner user"
useradd -m -s /bin/bash runner
usermod -aG docker runner

# Create runner directory
RUNNER_DIR="/home/runner/actions-runner"
mkdir -p $RUNNER_DIR
cd $RUNNER_DIR

# Download GitHub Actions runner
log "Downloading GitHub Actions runner"
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/v//')
curl -o actions-runner-linux-x64-$RUNNER_VERSION.tar.gz -L https://github.com/actions/runner/releases/download/v$RUNNER_VERSION/actions-runner-linux-x64-$RUNNER_VERSION.tar.gz

# Extract runner
tar xzf ./actions-runner-linux-x64-$RUNNER_VERSION.tar.gz

# Set ownership
chown -R runner:runner /home/runner

# Get registration token
log "Getting GitHub registration token"
REGISTRATION_TOKEN=$(curl -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$GITHUB_ORG/$GITHUB_REPO/actions/runners/registration-token" | jq -r '.token')

# Generate unique runner name
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
RUNNER_NAME="$RUNNER_NAME_PREFIX-$INSTANCE_ID"

# Configure runner
log "Configuring GitHub Actions runner: $RUNNER_NAME"
sudo -u runner ./config.sh \
    --url "https://github.com/$GITHUB_ORG/$GITHUB_REPO" \
    --token "$REGISTRATION_TOKEN" \
    --name "$RUNNER_NAME" \
    --labels "self-hosted,Linux,X64,aws,cis-hardened" \
    --work "_work" \
    --unattended \
    --replace

# Install runner as a service
log "Installing runner as systemd service"
./svc.sh install runner
./svc.sh start

# Create cleanup script for runner removal
cat > /home/runner/cleanup.sh << 'EOF'
#!/bin/bash
cd /home/runner/actions-runner
./config.sh remove --token $(curl -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$GITHUB_ORG/$GITHUB_REPO/actions/runners/remove-token" | jq -r '.token')
EOF

chmod +x /home/runner/cleanup.sh

# Set up cleanup on shutdown
cat > /etc/systemd/system/runner-cleanup.service << EOF
[Unit]
Description=GitHub Runner Cleanup
DefaultDependencies=no
Before=shutdown.target reboot.target halt.target

[Service]
Type=oneshot
RemainAfterExit=true
ExecStart=/bin/true
ExecStop=/home/runner/cleanup.sh
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

systemctl enable runner-cleanup.service

# Install additional security tools
log "Installing additional security tools"

# Install and configure OSSEC
wget -q -O - https://updates.atomicorp.com/installers/atomic | bash
yum install ossec-hids-server -y || apt-get install ossec-hids-server -y

# Configure file integrity monitoring
cat > /var/ossec/etc/ossec.conf << EOF
<ossec_config>
  <global>
    <email_notification>no</email_notification>
  </global>
  
  <syscheck>
    <frequency>3600</frequency>
    <directories check_all="yes">/etc,/usr/bin,/usr/sbin</directories>
    <directories check_all="yes">/bin,/sbin</directories>
    <directories check_all="yes">/home/runner/actions-runner</directories>
  </syscheck>
  
  <rootcheck>
    <disabled>no</disabled>
  </rootcheck>
</ossec_config>
EOF

# Final security configurations
log "Applying final security configurations"

# Disable unused services
systemctl disable apache2 2>/dev/null || true
systemctl disable nginx 2>/dev/null || true
systemctl disable mysql 2>/dev/null || true
systemctl disable postgresql 2>/dev/null || true

# Set strict permissions on sensitive files
chmod 600 /etc/ssh/sshd_config
chmod 644 /etc/passwd
chmod 600 /etc/shadow
chmod 644 /etc/group
chmod 600 /etc/gshadow

# Configure SSH hardening
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/#Protocol 2/Protocol 2/' /etc/ssh/sshd_config
echo "AllowUsers runner ubuntu" >> /etc/ssh/sshd_config
systemctl restart sshd

# Set up log rotation
cat > /etc/logrotate.d/runner << EOF
/var/log/runner-setup.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

# Final system update and cleanup
apt-get autoremove -y
apt-get autoclean

log "GitHub Runner setup completed successfully"
log "Runner name: $RUNNER_NAME"
log "Instance ID: $INSTANCE_ID"
log "CIS hardening: $ENABLE_CIS_HARDENING"

# Send completion signal to CloudWatch
aws logs put-log-events \
    --region "$AWS_REGION" \
    --log-group-name "$CLOUDWATCH_LOG_GROUP" \
    --log-stream-name "$INSTANCE_ID/runner-setup" \
    --log-events timestamp=$(date +%s000),message="Runner setup completed successfully" || true

log "Setup script completed"
