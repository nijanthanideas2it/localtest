# Render.com Deployment Guide

## Prerequisites
- Render.com account
- PostgreSQL database already deployed on Render ✅
- Git repository with your code

## Step 1: Prepare Your Repository

Make sure your repository has the following files in the `backend/` directory:
- `requirements.txt` - Dependencies ✅
- `Procfile` - Start command ✅
- `app/main.py` - Main application file ✅

## Step 2: Deploy to Render.com

### Option A: Using Render Dashboard (Recommended)

1. **Go to Render Dashboard**
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Click "New +" → "Web Service"

2. **Connect Repository**
   - Connect your GitHub/GitLab repository
   - Select the repository containing your backend code

3. **Configure Service**
   - **Name**: `project-management-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend` (if your backend code is in a subdirectory)

4. **Environment Variables**
   Add the following environment variables:
   ```
   DATABASE_URL=postgresql://project_management_eaoe_user:EnNCBCl069GPZUOHFrAZBN9qO2NzNhCv@dpg-d285ofc9c44c73a3ng5g-a.oregon-postgres.render.com/project_management_eaoe
   SECRET_KEY=your_secret_key_here
   DEBUG=false
   HOST=0.0.0.0
   PORT=8000
   ALLOWED_HOSTS=["https://your-frontend-domain.onrender.com","http://localhost:3000"]
   DATABASE_ECHO=false
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   PASSWORD_MIN_LENGTH=8
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your application

### Option B: Using render.yaml (Advanced)

1. **Update render.yaml**
   - The `render.yaml` file is already configured with your database
   - Update `ALLOWED_HOSTS` with your frontend domain

2. **Deploy**
   - Push your code to GitHub
   - Render will automatically detect and deploy using the yaml configuration

## Step 3: Verify Deployment

1. **Check Build Logs**
   - Monitor the build process in Render dashboard
   - Ensure all dependencies install successfully

2. **Test Endpoints**
   - Health check: `https://your-app-name.onrender.com/health`
   - API docs: `https://your-app-name.onrender.com/docs`

3. **Database Migration**
   - If needed, run database migrations manually or add to build process

## Step 4: Configure CORS

Update the `ALLOWED_HOSTS` environment variable to include your frontend domain:
```
ALLOWED_HOSTS=["https://your-frontend-app.onrender.com","http://localhost:3000"]
```

## Troubleshooting

### Common Issues:

1. **Build Failures**
   - Check the build logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`
   - Verify Python version compatibility

2. **Database Connection Issues**
   - ✅ **FIXED**: Database URL is configured correctly
   - Verify database is accessible from Render
   - Ensure database is running and accessible

3. **CORS Issues**
   - Update `ALLOWED_HOSTS` with correct frontend URL
   - Ensure frontend is making requests to the correct backend URL

4. **Port Issues**
   - Render automatically sets the `PORT` environment variable
   - Use `$PORT` in your start command

### Environment Variables Reference:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ Configured: `postgresql://project_management_eaoe_user:...@dpg-d285ofc9c44c73a3ng5g-a.oregon-postgres.render.com/project_management_eaoe` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here` |
| `DEBUG` | Debug mode | `false` |
| `ALLOWED_HOSTS` | CORS allowed origins | `["https://frontend.onrender.com"]` |
| `PORT` | Port number (auto-set by Render) | `8000` |

## Next Steps

1. **Update Frontend**
   - Update your frontend to use the new backend URL
   - Test all API endpoints

2. **Monitor**
   - Set up logging and monitoring
   - Monitor application performance

3. **Scale**
   - Upgrade to paid plan if needed
   - Configure auto-scaling

## Support

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- Check build logs for specific error messages 
