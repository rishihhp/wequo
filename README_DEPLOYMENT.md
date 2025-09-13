# WeQuo - Render Deployment

Quick deployment guide for the WeQuo platform on Render.com.

## 🚀 Quick Start

### 1. Prerequisites

- GitHub repository with WeQuo code
- Render.com account
- FRED API key (get free at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html))

### 2. Deploy in 3 Steps

1. **Push to GitHub**

   ```bash
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

2. **Deploy on Render**

   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Use these settings:
     - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt && python scripts/init_data.py`
     - **Start Command**: `python app.py`
     - **Environment**: Python 3

3. **Add Environment Variables**
   - `FRED_API_KEY`: Your FRED API key
   - `SECRET_KEY`: Let Render generate this

### 3. Access Your App

- Main Platform: `https://your-app.onrender.com/`
- Authoring Dashboard: `https://your-app.onrender.com/authoring`
- Monitoring Dashboard: `https://your-app.onrender.com/monitoring`

## 📁 What's Included

- **Main App** (`app.py`): Combined Flask application
- **Render Config** (`render.yaml`): Deployment configuration
- **Dependencies** (`requirements.txt`): Python packages
- **Data Init** (`scripts/init_data.py`): Initializes data directories
- **Documentation** (`docs/DEPLOYMENT.md`): Detailed deployment guide

## 🔧 Features

- **Authoring Dashboard**: Create and manage weekly briefs
- **Monitoring Dashboard**: System health and data analytics
- **Data Pipeline**: Automated data collection from multiple sources
- **Version Control**: Track changes and collaborate
- **Search & Export**: Find and export data packages

## 📚 Documentation

- [Full Deployment Guide](docs/DEPLOYMENT.md)
- [Onboarding Guide](docs/ONBOARDING.md)
- [API Keys Setup](docs/DEPLOYMENT.md#api-keys)

## 🆘 Need Help?

1. Check the [deployment guide](docs/DEPLOYMENT.md) for detailed instructions
2. Review application logs in Render dashboard
3. Use the health check endpoint: `/health`
4. Monitor system status in the monitoring dashboard

---

**Ready to deploy?** Run `./deploy.sh` for a guided setup!
