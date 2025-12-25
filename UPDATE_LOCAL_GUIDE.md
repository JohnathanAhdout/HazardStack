# 🔄 Update Your Local SPIRAL with New Changes

Quick guide to pull the latest changes I just committed to your local machine.

---

## ✅ Quick Update (If You're Already on the Branch)

```bash
# Make sure you're in the SPIRAL directory
cd /home/user/SPIRAL

# Check which branch you're on
git branch

# If you're on claude/add-missing-functionality-5ntUT, just pull:
git pull origin claude/add-missing-functionality-5ntUT
```

---

## 📥 Full Update Steps (Recommended)

### Step 1: Check Your Current Status

```bash
# Navigate to SPIRAL directory
cd /home/user/SPIRAL

# Check current branch
git branch

# Check for any local changes
git status
```

### Step 2: Save Any Local Changes (If You Have Them)

```bash
# If you made any local changes, save them:
git stash

# Or commit them:
git add .
git commit -m "My local changes"
```

### Step 3: Fetch Latest Changes from GitHub

```bash
# Fetch all branches and updates
git fetch origin

# You should see:
# From https://github.com/JohnathanAhdout/SPIRAL
#  * [new branch]      claude/add-missing-functionality-5ntUT -> origin/claude/add-missing-functionality-5ntUT
```

### Step 4: Switch to the New Branch

```bash
# Switch to the feature branch
git checkout claude/add-missing-functionality-5ntUT

# Or if it doesn't exist locally yet:
git checkout -b claude/add-missing-functionality-5ntUT origin/claude/add-missing-functionality-5ntUT
```

### Step 5: Pull Latest Changes

```bash
# Pull all the new commits
git pull origin claude/add-missing-functionality-5ntUT

# You should see:
# Updating XXXXX..271a666
# Fast-forward
#  17 files changed, 1938 insertions(+), 140 deletions(-)
#  create mode 100644 hazardstack/api/services/__init__.py
#  create mode 100644 hazardstack/api/services/earthquake_service.py
#  create mode 100644 web-app/app/about/page.tsx
#  create mode 100644 web-app/app/alerts/page.tsx
#  create mode 100644 web-app/app/analytics/page.tsx
#  create mode 100644 web-app/app/dashboard/page.tsx
#  create mode 100644 web-app/app/notifications/page.tsx
#  create mode 100644 web-app/app/settings/page.tsx
```

### Step 6: Verify You Have the Latest Code

```bash
# Check the latest commit
git log --oneline -1

# Should show:
# 271a666 Add comprehensive website functionality with real data integration

# Check what files changed
git diff HEAD~1 --name-only

# Or see detailed commit info
git show --stat
```

---

## 🆕 What's New in This Update

After pulling, you'll have these new features:

### New Files Created:
```
✅ hazardstack/api/services/earthquake_service.py
✅ hazardstack/api/services/__init__.py
✅ web-app/app/dashboard/page.tsx
✅ web-app/app/alerts/page.tsx
✅ web-app/app/analytics/page.tsx
✅ web-app/app/about/page.tsx
✅ web-app/app/settings/page.tsx
✅ web-app/app/notifications/page.tsx
```

### Modified Files:
```
✅ hazardstack/api/routes/events.py (now fetches real USGS data)
✅ hazardstack/api/routes/risk.py (tile generation implemented)
✅ hazardstack/api/routes/health.py (enhanced readiness checks)
✅ web-app/components/Header.tsx (working navigation)
✅ web-app/components/MapView.tsx (interactive clicking)
✅ web-app/components/AlertsList.tsx (handles both earthquakes and floods)
✅ web-app/components/StatsOverview.tsx (calculated statistics)
✅ web-app/lib/api.ts (updated data fetching)
✅ web-app/app/page.tsx (redirects to dashboard)
```

---

## 🔍 Verify Everything Pulled Correctly

### Check if new pages exist:

```bash
# Check if new pages were created
ls -la web-app/app/dashboard/
ls -la web-app/app/alerts/
ls -la web-app/app/analytics/
ls -la web-app/app/about/
ls -la web-app/app/settings/
ls -la web-app/app/notifications/

# Check if earthquake service exists
ls -la hazardstack/api/services/
```

### Check file content:

```bash
# View the new earthquake service
cat hazardstack/api/services/earthquake_service.py | head -20

# View the new dashboard page
cat web-app/app/dashboard/page.tsx | head -20
```

---

## 🚀 After Updating: Reinstall Dependencies

Since new packages may have been added, reinstall dependencies:

### For Web App:

```bash
cd web-app

# Remove old dependencies
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### For Backend API:

```bash
# The backend uses httpx now for USGS API
pip3 install httpx

# Or reinstall all
pip3 install -r requirements.txt
```

---

## 🎯 Quick Test After Update

### Test 1: Check Git Status

```bash
git status
# Should say: "Your branch is up to date with 'origin/claude/add-missing-functionality-5ntUT'"
```

### Test 2: Run Web App

```bash
cd web-app
npm run dev
```

Open http://localhost:3000 → Should redirect to /dashboard

### Test 3: Check New Pages

- http://localhost:3000/dashboard
- http://localhost:3000/alerts
- http://localhost:3000/analytics
- http://localhost:3000/about
- http://localhost:3000/settings
- http://localhost:3000/notifications

### Test 4: Run Backend

```bash
cd hazardstack
python3 -m uvicorn api.main:app --reload
```

Try: http://localhost:8000/api/v1/events/recent

---

## 🐛 Troubleshooting

### "Already up to date" but I don't see new files

```bash
# Force fetch all branches
git fetch --all

# Hard reset to remote branch (⚠️ This will discard local changes!)
git reset --hard origin/claude/add-missing-functionality-5ntUT
```

### "Your local changes would be overwritten"

```bash
# Save your changes first
git stash

# Then pull
git pull origin claude/add-missing-functionality-5ntUT

# Apply your changes back
git stash pop
```

### "fatal: refusing to merge unrelated histories"

```bash
# This shouldn't happen, but if it does:
git pull origin claude/add-missing-functionality-5ntUT --allow-unrelated-histories
```

### Can't find the branch

```bash
# List all remote branches
git branch -r

# If you see the branch but can't switch:
git fetch origin
git checkout -t origin/claude/add-missing-functionality-5ntUT
```

---

## 📊 View Commit Details

```bash
# See the full commit message
git log -1

# See what changed
git show 271a666

# See file differences
git diff HEAD~1

# See files changed with stats
git diff HEAD~1 --stat
```

---

## 🔀 Alternative: Download ZIP (If Git Issues)

If you're having git trouble, you can download the branch directly:

1. Go to: https://github.com/JohnathanAhdout/SPIRAL
2. Click "Branch: main" dropdown
3. Select "claude/add-missing-functionality-5ntUT"
4. Click "Code" → "Download ZIP"
5. Extract and replace your local files

---

## ✅ Verification Checklist

After updating, verify:

- [ ] `git status` shows "up to date"
- [ ] `git log -1` shows commit "271a666"
- [ ] New pages exist in `web-app/app/`
- [ ] Earthquake service exists in `hazardstack/api/services/`
- [ ] `npm install` completes successfully
- [ ] Web app starts without errors
- [ ] Backend API starts without errors
- [ ] Can navigate to /dashboard, /alerts, etc.

---

**You're all set! 🎉**

Now follow the [LOCAL_LAUNCH_GUIDE.md](LOCAL_LAUNCH_GUIDE.md) to run the application.
