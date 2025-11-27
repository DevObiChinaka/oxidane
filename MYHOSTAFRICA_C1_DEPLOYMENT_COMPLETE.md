# MyHostAfrica C1 Plan Deployment Guide
# Complete deployment package for oxiworldforexacademy.com
# ======================================================

## Overview
This deployment package is optimized for MyHostAfrica's C1 plan:
- **VPS Specifications**: 1 vCPU, 2GB RAM, 30GB SSD
- **Operating System**: Ubuntu 22.04 LTS
- **Domain**: oxiworldforexacademy.com
- **Total Monthly Cost**: ~₦15,000 - ₦20,000

## C1 Plan Optimizations

### Resource Allocation
- **Gunicorn**: 2 workers, 2 threads (512MB memory limit)
- **Celery**: 2 concurrent workers (256MB memory limit)
- **PostgreSQL**: Optimized for 2GB RAM (256MB shared_buffers)
- **Redis**: Limited to 256MB with LRU eviction
- **Nginx**: Single worker process optimization
- **Swap**: 1GB swap file for memory assistance

### Performance Tunings
- Conservative connection pooling
- Aggressive log rotation (7 days, 20MB max)
- Gzip compression level 4 (CPU efficient)
- Rate limiting configured
- Memory-conscious buffer sizes

## Files Included

### Core Deployment Files
1. **myhostafrica_c1_setup.sh** - VPS setup and system configuration
2. **deploy_myhostafrica_c1.sh** - Application deployment script
3. **myhostafrica_c1_production.env** - Environment configuration template
4. **nginx_myhostafrica_c1.conf** - Nginx configuration for C1
5. **myhostafrica_c1_deploy_guide.sh** - Step-by-step deployment guide

### Existing Configuration Files (Updated)
- **backend/oxidane/settings.py** - Django settings for oxiworldforexacademy.com
- **nginx_oxidane.conf** - Standard nginx configuration
- **.env.template** - Environment variables template

## Deployment Steps

### Step 1: VPS Purchase and Setup
```bash
1. Login to MyHostAfrica control panel
2. Purchase C1 Plan VPS (1 vCPU, 2GB RAM, 30GB SSD)
3. Choose Ubuntu 22.04 LTS
4. Set root password and SSH key
5. Note VPS IP address
```

### Step 2: DNS Configuration
```bash
# Configure A records in MyHostAfrica DNS:
A Record: oxiworldforexacademy.com → YOUR_VPS_IP
A Record: www.oxiworldforexacademy.com → YOUR_VPS_IP
```

### Step 3: Server Setup
```bash
# SSH into VPS
ssh root@YOUR_VPS_IP

# Run C1-optimized setup
curl -sSL https://raw.githubusercontent.com/DevObiChinaka/oxidane/mySaaS/myhostafrica_c1_setup.sh | bash
```

### Step 4: Application Deployment
```bash
# Switch to application user
su - oxidane

# Clone repository
cd /var/www/oxidane
git clone https://github.com/DevObiChinaka/oxidane.git .

# Run C1-optimized deployment
bash deploy_myhostafrica_c1.sh
```

### Step 5: SSL Configuration
```bash
# Install SSL certificate
sudo certbot --nginx -d oxiworldforexacademy.com -d www.oxiworldforexacademy.com
```

## C1 Resource Monitoring

### Essential Monitoring Commands
```bash
# Resource overview
/usr/local/bin/oxidane-c1-monitor.sh

# Memory usage
free -h

# Disk usage
df -h

# Service status
systemctl status oxidane-gunicorn oxidane-celery nginx

# Real-time monitoring
htop
nload
iotop
```

### Warning Thresholds
- **Memory**: Warning at 75%, Critical at 90%
- **Disk**: Warning at 80%, Critical at 90%
- **Swap Usage**: Should be minimal (<10%)

## C1 Limitations and Recommendations

### Known Limitations
- **Concurrent Users**: ~50-100 simultaneous users
- **File Uploads**: Limited to 10MB
- **Database**: Small to medium datasets
- **Background Tasks**: Light processing only

### When to Upgrade to C2/C3
- Memory consistently >80%
- High swap usage (>500MB)
- Response times >3 seconds
- Database query timeouts
- Failed Celery tasks due to memory

## Cost Analysis

### Monthly Costs (Estimated)
- **C1 VPS**: ₦12,000 - ₦15,000
- **Domain Renewal**: ₦3,000 - ₦5,000
- **SSL Certificate**: Free (Let's Encrypt)
- **Total**: ₦15,000 - ₦20,000/month

### Cost Optimization Tips
- Regular cleanup of logs and temporary files
- Optimize images and media files
- Use CDN for static assets (if needed)
- Monitor resource usage to avoid over-provisioning

## Security Configuration

### Implemented Security
- UFW firewall with minimal open ports
- Fail2ban for intrusion prevention
- SSL/TLS with modern cipher suites
- Rate limiting on API endpoints
- Security headers in Nginx
- Regular security updates

### Security Checklist
- [ ] Change default passwords
- [ ] Configure SSH key authentication
- [ ] Enable automatic security updates
- [ ] Set up backup strategy
- [ ] Configure monitoring alerts

## Backup Strategy

### Recommended Backups
1. **Database**: Daily PostgreSQL dumps
2. **Media Files**: Weekly backup to external storage
3. **Configuration**: Monthly full system snapshot
4. **Code**: Git repository (already handled)

### Backup Commands
```bash
# Database backup
sudo -u postgres pg_dump oxidane_prod > backup_$(date +%Y%m%d).sql

# Media backup (if using external storage)
rsync -av /var/www/oxidane/media/ backup-server:/backups/oxidane/media/
```

## Troubleshooting

### Common C1 Issues
1. **High Memory Usage**
   - Check: `free -h`
   - Solution: Restart services, check for memory leaks

2. **Slow Response Times**
   - Check: `htop`, service logs
   - Solution: Optimize database queries, restart services

3. **Disk Space Issues**
   - Check: `df -h`
   - Solution: Clean logs, optimize media files

4. **Service Crashes**
   - Check: `journalctl -fu oxidane-gunicorn`
   - Solution: Check memory limits, restart services

### Quick Fixes
```bash
# Restart all services
sudo systemctl restart oxidane-gunicorn oxidane-celery nginx

# Clear logs
sudo logrotate -f /etc/logrotate.d/oxidane

# Check service health
systemctl status oxidane-gunicorn oxidane-celery nginx postgresql redis-server
```

## Support and Maintenance

### MyHostAfrica Support
- 24/7 technical support available
- Control panel for VPS management
- Resource monitoring tools
- Automatic security updates

### Maintenance Schedule
- **Daily**: Monitor resource usage
- **Weekly**: Check service logs, update packages
- **Monthly**: Full system update, backup verification
- **Quarterly**: Security audit, performance review

## Success Metrics

### Performance Targets (C1)
- **Page Load Time**: <3 seconds
- **API Response Time**: <1 second
- **Uptime**: >99.5%
- **Memory Usage**: <80% average
- **Disk Usage**: <80%

### Monitoring Tools
- Built-in C1 resource monitor script
- System logs and service monitoring
- MyHostAfrica control panel metrics
- Custom alerting for resource thresholds

---

## Ready for Production!

Your OxiWorld Forex Academy application is now optimized and ready for deployment on MyHostAfrica's C1 plan. The configuration provides a solid foundation for a growing business while maintaining cost efficiency.

**Next Action**: Purchase C1 VPS and follow the deployment steps above.

For questions or issues, refer to the troubleshooting section or contact MyHostAfrica support.