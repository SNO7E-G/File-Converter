# File Converter

<div align="center">
  <h3>A powerful and flexible file conversion platform</h3>

  ![GitHub License](https://img.shields.io/github/license/SNO7E-G/file-converter)
  ![React](https://img.shields.io/badge/React-18.2+-61DAFB?logo=react&logoColor=white)
  ![Flask](https://img.shields.io/badge/Flask-2.2.3-000000?logo=flask&logoColor=white)
  ![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
  ![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?logo=typescript&logoColor=white)
  ![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
</div>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#algorithms">Algorithms</a> •
  <a href="#api-reference">API Reference</a> •
  <a href="#troubleshooting">Troubleshooting</a> •
  <a href="#roadmap">Roadmap</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>


## Features

- **Versatile File Conversion**: Convert between multiple formats including documents, images, audio, and video
- **Chained Conversions**: Smart multi-step conversions when direct conversion isn't available
- **User Tiers**: Free and premium tiers with different daily conversion limits
- **Scheduled Conversions**: Schedule conversions to run at specific times
- **Secure Authentication**: User management with password hashing and JWT authentication
- **Responsive Design**: Optimized for both desktop and mobile devices
- **Conversion History**: Track all your previous conversions
- **File Sharing**: Share converted files with other users via secure links
- **Webhook Notifications**: Get notified when conversions complete
- **Conversion Statistics**: View detailed metrics about your conversion history
- **Multiple Database Support**: Works with PostgreSQL, MySQL, and MongoDB
- **Flexible Storage Options**: Store files locally, or in S3, Google Cloud Storage, or Azure Blob Storage
- **Advanced Data Organization**: Sort, filter, and group conversions with various algorithms
- **Docker Deployment**: Easy deployment with Docker Compose for all components
- **Batch Processing**: Convert multiple files simultaneously
- **Auto-retry Mechanism**: Automatically retry failed conversions with exponential backoff
- **Optimized Conversion Paths**: Intelligently select the most efficient conversion chain

## Tech Stack

### Frontend
- **React 18+**: UI library for building interactive interfaces
- **TypeScript 5+**: Type-safe JavaScript for better developer experience
- **Material UI 5+**: Modern component library for a polished UI
- **TailwindCSS 3+**: Utility-first CSS framework for responsive design
- **React Router 6+**: Navigation and routing for single page applications
- **Axios**: Promise-based HTTP client for API requests
- **React Context API**: State management across components
- **React Query**: Data fetching and caching library
- **Chart.js**: Interactive charts for analytics

### Backend
- **Python 3.8+**: Core programming language for the backend
- **Flask 2+**: Web framework for building the REST API
- **SQLAlchemy 2+**: ORM for database access
- **Multiple Databases**: 
  - PostgreSQL 14+ (default)
  - MySQL 8+
  - MongoDB 5+
  - SQLite (for development)
- **Celery 5+**: Task queue for handling asynchronous conversions
- **Redis 6+**: Caching and message broker for Celery
- **JWT**: Secure authentication tokens
- **Flask-Limiter**: Rate limiting for API endpoints

### File Storage
- **Local Filesystem**: Default storage for development
- **AWS S3**: Scalable cloud storage (also works with MinIO)
- **Google Cloud Storage**: Integration with GCP
- **Azure Blob Storage**: Integration with Azure

### File Processing
- **Pandas**: Data manipulation for document conversions
- **FFmpeg**: Audio and video conversion
- **Pillow**: Image processing
- **PyPDF2/ReportLab**: PDF generation and manipulation
- **Librosa**: Audio processing
- **NumPy**: Numerical operations for data processing

### DevOps
- **Docker**: Containerization for consistent environments
- **Docker Compose**: Multi-container application orchestration
- **GitHub Actions**: CI/CD pipeline for automated testing and deployment
- **Prometheus/Grafana**: Monitoring and alerting (optional)

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │      │   Backend API   │      │   Celery        │
│   (React)       │◄────►│   (Flask)       │◄────►│   Workers       │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                │                         │
                                ▼                         ▼
┌───────────────────────────────────────────┐   ┌─────────────────┐
│              Databases                     │   │   Redis         │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │   Queue/Cache   │
│ │PostgreSQL│ │  MySQL   │ │ MongoDB  │    │   └─────────────────┘
│ └──────────┘ └──────────┘ └──────────┘    │           │
└───────────────────────────────────────────┘           ▼
                                               ┌─────────────────────┐
                                               │   Storage Backends  │
                                               │ ┌─────┐┌────┐┌─────┐│
                                               │ │Local││ S3 ││Azure ││
                                               │ └─────┘└────┘└─────┘│
                                               └─────────────────────┘
```

### Key Components:

- **Converter Factory**: Creates appropriate converters based on file formats using the Factory pattern
- **Base Converter**: Abstract class that all converters extend (Template Method pattern)
- **Format-Specific Converters**: Specialized converters for different file types
- **Chained Converter**: Handles multi-step conversions when direct conversion isn't possible (Chain of Responsibility pattern)
- **User Model**: Manages user authentication, tiers, and settings
- **Conversion Model**: Tracks conversion tasks, file locations, and sharing
- **Storage Handlers**: Abstraction for different storage backends (Strategy pattern)
- **Data Sorter**: Provides algorithms for sorting, filtering, and grouping conversion data

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js (v16 or higher)
- Docker and Docker Compose (recommended)
- FFmpeg (for audio/video conversions)
- Git

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/SNO7E-G/file-converter.git
   cd file-converter
   ```

2. Create a `.env` file for configuration:
   ```bash
   cp .env.example .env
   # Edit .env file to configure database and storage options
   ```

3. Start the application with your chosen database and storage:
   ```bash
   # Use PostgreSQL (default)
   docker-compose up -d
   
   # Use MySQL
   docker-compose --profile mysql up -d
   
   # Use MongoDB
   docker-compose --profile mongodb up -d
   
   # Use S3-compatible storage (MinIO)
   docker-compose --profile s3 up -d
   
   # Run with all databases and storage options
   docker-compose --profile all up -d
   
   # Include admin tools (phpMyAdmin, pgAdmin, MongoDB Express)
   docker-compose --profile tools up -d
   ```

4. The application will be available at:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Swagger API Docs: http://localhost:8000/api/docs
   - pgAdmin (PostgreSQL management): http://localhost:5050
   - phpMyAdmin (MySQL management): http://localhost:5051
   - MongoDB Express: http://localhost:5052
   - MinIO Console: http://localhost:9001

5. Initialize the database and create an admin user:
   ```bash
   # Enter the backend container
   docker-compose exec api bash
   
   # Run initialization scripts
   python -m init_db
   python -m create_admin --username admin --password securepassword --email admin@example.com
   
   # Exit the container
   exit
   ```

### Manual Setup

#### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

5. Start the Flask server:
   ```bash
   flask run --host=0.0.0.0 --port=8000
   ```

#### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create an environment file:
   ```bash
   cp .env.example .env.local
   # Edit .env.local to set the backend API URL
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. The frontend will be available at http://localhost:3000

## Usage

### Basic File Conversion

1. Log in to your account or sign up for a new one
2. Click on "Convert" in the sidebar menu
3. Drag and drop your file or click to browse
4. Select the target format
5. Configure conversion options (if available)
6. Click "Convert" to start the process
7. Once complete, download your converted file

### Batch Conversion

1. Navigate to "Batch Convert"
2. Upload multiple files
3. Select the target format for each file (or use the same format for all)
4. Start the batch conversion
5. Monitor progress and download files individually or as a ZIP archive

### Scheduled Conversions

1. Navigate to "Schedule"
2. Upload your file
3. Select the target format
4. Choose the date and time for conversion
5. Optionally set up webhook notifications
6. Save the scheduled task
7. The system will process the conversion at the specified time

### Templates

1. Navigate to "Templates"
2. Create a new template with your preferred conversion settings
3. Name and save the template
4. Use the template for future conversions to maintain consistent settings

### Sharing Conversions

1. Navigate to "History" or "Dashboard"
2. Find the conversion to share
3. Click "Share" and specify the recipient's email or username
4. Choose permission level (view, download, or edit)
5. The recipient will receive a notification

## API Reference

The backend provides a RESTful API for all operations. Full OpenAPI/Swagger documentation is available at `/api/docs` when the application is running.

### Authentication

```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/logout
```

### Conversions

```
POST /api/upload
GET /api/conversions
GET /api/conversions/{id}
GET /api/conversions/{id}/download
POST /api/conversions/{id}/share
```

### Formats

```
GET /api/formats
GET /api/formats/conversions
GET /api/formats/options
```

## Troubleshooting

### Common Issues

- **Conversion fails**: Check if the source file is valid and not corrupted
- **Database connection errors**: Verify database credentials in .env file
- **Storage errors**: Ensure proper permissions for the upload directory
- **CORS issues**: Check CORS configuration if frontend can't connect to backend
- **Missing FFmpeg**: Install FFmpeg for audio/video conversions

### Logs

- Backend logs are located in `backend/logs`
- Docker logs can be viewed with `docker-compose logs -f <service-name>`

## Roadmap

- [ ] Add support for additional file formats
- [ ] Implement OCR capabilities for document conversion
- [ ] Create mobile applications (iOS/Android)
- [ ] Integrate with more cloud storage providers
- [ ] Add advanced AI-based image/audio processing options
- [ ] Implement user subscription management
- [ ] Add internationalization support
- [ ] Improve accessibility features

## Contributing

We welcome contributions to the File Converter project! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [FFmpeg](https://ffmpeg.org/) for audio/video processing
- [Pillow](https://python-pillow.org/) for image processing
- [PyPDF2](https://pypdf2.readthedocs.io/) for PDF processing
- [React](https://reactjs.org/) for the frontend framework
- [Flask](https://flask.palletsprojects.com/) for the backend framework 