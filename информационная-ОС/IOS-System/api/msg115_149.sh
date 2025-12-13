# If vulnerability identified, apply patch immediately

# 1. Emergency patch
git checkout -b security-patch-$(date +%Y%m%d)
# Apply fix
git commit -m "SECURITY: Fix [vulnerability description]"
git push

# 2. Build new image
docker build -t ios-system/api:security-patch-$(date +%Y%m%d) .
docker push ios-system/api:security-patch-$(date +%Y%m%d)

# 3. Deploy immediately
kubectl set image deployment/ios-api -n ios-production \
  api=ios-system/api:security-patch-$(date +%Y%m%d)

# 4. Verify patch
./scripts/security/verify-patch.sh