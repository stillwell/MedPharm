#!/bin/bash
# MedPharm ERP - Docker health check script
curl -sf http://localhost:80/api/v1/health > /dev/null 2>&1 || exit 1
