# 🚀 LeafIQ Deployment Guide

## **Option 1: Render (Free & Recommended)**

### Step 1: Prepare Your Repository
```bash
# Commit all changes
git add .
git commit -m "Prepare for deployment: Add Procfile and gunicorn"
git push origin main
```

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New" → "Web Service"
3. Connect your GitHub repository: `AI-Powered-Plant-Disease-Detection-System`
4. Configure:
   - **Name**: `leafiq-plant-disease-detection`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`

### Step 3: Set Environment Variables
In Render dashboard, go to Environment tab and add:
```
GEMINI_API_KEY=your_gemini_key_here
GOOGLE_API_KEY=your_google_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_id_here
PLANTNET_API_KEY=your_plantnet_key_here
```

### Step 4: Deploy!
- Click "Create Web Service"
- Wait 5-10 minutes for build
- Your app will be live at: `https://leafiq-plant-disease-detection.onrender.com`

---

## **Option 2: Railway (Alternative Free Option)**

### Step 1: Railway Setup
1. Go to [railway.app](https://railway.app) and login with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway auto-detects Python and Flask

### Step 2: Environment Variables
Add your API keys in Railway dashboard under Variables tab

### Step 3: Custom Domain (Optional)
- Railway provides: `your-app-name.up.railway.app`
- Can add custom domain in settings

---

## **Option 3: Heroku (Paid)**

### Step 1: Heroku CLI
```bash
# Install Heroku CLI, then:
heroku create leafiq-plant-detection
heroku config:set GEMINI_API_KEY=your_key_here
heroku config:set GOOGLE_API_KEY=your_key_here
# ... add other API keys

git push heroku main
```

---

## **Option 4: Vercel (Serverless)**

### Step 1: Create vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
```

### Step 2: Deploy
```bash
npm i -g vercel
vercel --prod
```

---

## **Option 5: PythonAnywhere (Simple)**

### Step 1: Upload Files
1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload your project files via Files tab
3. Install requirements in Bash console:
   ```bash
   pip3.10 install --user -r requirements.txt
   ```

### Step 2: Configure Web App
1. Go to Web tab → "Add a new web app"
2. Choose Flask
3. Set source code path to your app.py
4. Add environment variables in .env file

---

## **🎯 Recommended Approach: Render**

**Why Render?**
- ✅ **Free tier** with generous limits
- ✅ **Easy setup** - just connect GitHub
- ✅ **Automatic deploys** on git push
- ✅ **HTTPS** included
- ✅ **Good performance** for AI apps
- ✅ **Environment variables** support
- ✅ **Build logs** for debugging

**Render Free Tier:**
- 512MB RAM
- Shared CPU
- 100GB bandwidth/month
- Automatic SSL
- Custom domains

---

## **🔧 Deployment Checklist**

### Before Deployment:
- [x] Procfile created
- [x] requirements.txt updated with gunicorn
- [x] Environment variables documented
- [x] Git repository up to date
- [ ] Test locally with gunicorn: `gunicorn app:app`

### After Deployment:
- [ ] Test all features (upload, camera, detection)
- [ ] Verify API integrations work
- [ ] Check error logs if issues
- [ ] Update README with live URL
- [ ] Share your deployed app! 🎉

---

## **📱 Testing Your Deployment**

### Local Testing with Gunicorn:
```bash
# Test production server locally
gunicorn app:app --bind 0.0.0.0:5000

# Test in browser: http://localhost:5000
```

### Post-Deployment Tests:
1. **Image Upload**: Test drag & drop functionality
2. **Camera Capture**: Test live photo capture
3. **Disease Detection**: Upload test images from `/test` folder
4. **API Integration**: Verify Gemini AI responses
5. **Mobile Compatibility**: Test on phone/tablet
6. **Error Handling**: Test with invalid images

---

## **🚨 Troubleshooting**

### Common Issues:
1. **Build Fails**: Check requirements.txt and Python version
2. **App Won't Start**: Verify Procfile and gunicorn installation
3. **API Errors**: Check environment variables are set
4. **Model Loading**: Ensure model/best.pt is in repository
5. **Memory Issues**: AI models need sufficient RAM

### Debug Commands:
```bash
# Check deployment logs
# (Available in your hosting platform's dashboard)

# Test API keys locally
python test_all_apis.py

# Verify model loading
python -c "from ultralytics import YOLO; YOLO('model/best.pt')"
```

---

## **🌟 Next Steps**

After successful deployment:
1. **Custom Domain**: Point your domain to the app
2. **Analytics**: Add Google Analytics for usage tracking
3. **Monitoring**: Set up uptime monitoring
4. **CDN**: Use CDN for faster image loading
5. **Database**: Add user accounts and history
6. **API Rate Limiting**: Implement usage limits
7. **Mobile App**: Create React Native/Flutter app

---

**🎉 Ready to deploy? Start with Render - it's the easiest option for your LeafIQ project!**
