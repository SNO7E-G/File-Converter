# Contributing to File Converter

Thank you for your interest in contributing to the File Converter project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Contributing Code](#contributing-code)
- [Development Environment Setup](#development-environment-setup)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Using Docker](#using-docker)
  - [Troubleshooting](#troubleshooting)
- [Development Guidelines](#development-guidelines)
  - [Code Style](#code-style)
  - [Testing](#testing)
  - [Commit Messages](#commit-messages)
  - [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
  - [PR Template](#pr-template)
  - [Code Review](#code-review)
  - [CI/CD Process](#cicd-process)
- [Architecture Guidelines](#architecture-guidelines)
  - [Frontend Architecture](#frontend-architecture)
  - [Backend Architecture](#backend-architecture)
  - [Creating a New Converter](#creating-a-new-converter)
- [License](#license)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How to Contribute

### Reporting Bugs

Before submitting a bug report:

1. Check the [GitHub issues](https://github.com/SNO7E-G/file-converter/issues) to avoid duplicates
2. Ensure the bug is reproducible with the latest version
3. Fill out the bug report template with as much detail as possible, including:
   - A clear description of the bug
   - Steps to reproduce
   - Expected behavior
   - Screenshots if applicable
   - Environment details (OS, browser, device, etc.)
   - Any error messages or logs

### Suggesting Features

We welcome feature suggestions! To suggest a feature:

1. Check existing issues to ensure your suggestion is not a duplicate
2. Create a new issue using the feature request template
3. Clearly describe the feature and its use case
4. Explain how the feature benefits the project and its users
5. If possible, include mockups, diagrams, or examples

### Contributing Code

1. **Fork the repository**

2. **Clone your fork**
    ```bash
    git clone https://github.com/SNO7E-G/file-converter.git
    cd file-converter
    ```

3. **Create a new branch**
    ```bash
    git checkout -b feature/your-feature-name
    ```
   Use a descriptive branch name following the convention:
   - `feature/` - for new features
   - `fix/` - for bug fixes
   - `docs/` - for documentation updates
   - `test/` - for test improvements
   - `refactor/` - for code refactoring

4. **Set up the development environment** (see [Development Environment Setup](#development-environment-setup) below)

5. **Make your changes**
    - Follow the coding style of the project
    - Add tests for your changes when applicable
    - Write meaningful commit messages

6. **Run tests to ensure your changes don't break existing functionality**

7. **Push your changes**
    ```bash
    git push origin feature/your-feature-name
    ```

8. **Create a Pull Request**
    - Go to the [repository](https://github.com/SNO7E-G/file-converter)
    - Click "Pull Requests" > "New Pull Request"
    - Select your fork and branch
    - Fill out the PR template

## Development Environment Setup

### Prerequisites

Make sure you have the following installed:

- Python 3.8 or higher
- Node.js 16 or higher and npm
- Git
- Docker and Docker Compose (optional, but recommended)
- FFmpeg (required for audio/video conversions)

### Backend Setup

1. Navigate to the backend directory
    ```bash
    cd backend
    ```

2. Create and activate a virtual environment
    ```bash
    python -m venv venv
    
    # On Windows
    venv\Scripts\activate
    
    # On macOS/Linux
    source venv/bin/activate
    ```

3. Install dependencies
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt  # Development dependencies
    ```

4. Create local environment file
    ```bash
    cp .env.example .env
    ```
    Edit the .env file to configure:
    - Database connection (SQLite by default for development)
    - Storage settings
    - JWT secret keys
    - Other application settings

5. Initialize the database
    ```bash
    flask db upgrade
    ```

6. Create a test admin user (optional)
    ```bash
    python -m scripts.create_admin --username admin --password secure_password --email admin@example.com
    ```

7. Run the development server
    ```bash
    flask run --debug
    ```
    The API will be available at http://localhost:5000

8. In a separate terminal, start the Celery worker
    ```bash
    celery -A app.tasks.celery worker --loglevel=info
    ```

### Frontend Setup

1. Navigate to the frontend directory
    ```bash
    cd frontend
    ```

2. Install dependencies
    ```bash
    npm install
    ```

3. Create local environment file
    ```bash
    cp .env.example .env.local
    ```
    Set `REACT_APP_API_URL` to your backend URL (usually http://localhost:5000 for development)

4. Run the development server
    ```bash
    npm run dev
    ```
    The frontend will be available at http://localhost:3000

### Using Docker

For a complete development environment with all services:

1. From the project root, build and start the containers
    ```bash
    docker-compose -f docker-compose.dev.yml up -d
    ```

2. The services will be available at:
    - Frontend: http://localhost:3000
    - Backend API: http://localhost:8000
    - PostgreSQL: localhost:5432
    - Redis: localhost:6379
    - MinIO (S3): http://localhost:9000 (console at http://localhost:9001)

3. To view logs
    ```bash
    docker-compose -f docker-compose.dev.yml logs -f
    ```

4. To stop the services
    ```bash
    docker-compose -f docker-compose.dev.yml down
    ```

### Troubleshooting

**Backend Issues**

- **Database connection errors**: Check your database configuration in the `.env` file
- **ModuleNotFoundError**: Ensure you've activated the virtual environment and installed all dependencies
- **Permission errors with file uploads**: Check the permissions on the upload directory
- **FFmpeg errors**: Ensure FFmpeg is installed and available in your PATH

**Frontend Issues**

- **API connection errors**: Verify the `REACT_APP_API_URL` in your `.env.local` file
- **Node module errors**: Try deleting `node_modules` folder and `package-lock.json`, then run `npm install` again
- **TypeScript errors**: Run `npm run tsc` to check for type errors

**Docker Issues**

- **Port conflicts**: Ensure no other services are using the required ports
- **Container startup failures**: Check the logs with `docker-compose logs <service_name>`
- **Volume permission issues**: Check file permissions on mounted volumes

## Development Guidelines

### Code Style

- **Python**: 
  - Follow PEP 8 style guidelines
  - Use Flake8 for linting
  - Maximum line length is 100 characters
  - Use type annotations where appropriate
  ```bash
  # Check code style
  flake8
  ```

- **JavaScript/TypeScript**: 
  - Follow the ESLint and Prettier configuration
  - Use TypeScript interfaces for type definitions
  - Keep components modular and focused
  ```bash
  # Check code style
  npm run lint
  ```

### Testing

All new features should include appropriate tests:

- **Backend Tests**: 
  ```bash
  # Run all tests
  pytest
  
  # Run tests with coverage report
  pytest --cov=app --cov-report=html
  ```

- **Frontend Tests**:
  ```bash
  # Run all tests
  npm test
  
  # Run tests in watch mode
  npm test -- --watch
  
  # Run tests with coverage
  npm test -- --coverage
  ```

Test requirements:
- Unit tests for services, utilities, and helpers
- Integration tests for API endpoints
- Component tests for React components
- End-to-end tests for critical user flows

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Routine tasks, maintenance, etc.

Example:
```
feat(converter): add support for HEIC image format

- Implement HEIC to JPEG/PNG conversion
- Add unit tests for HEIC converter
- Update documentation

Closes #123
```

### Documentation

- Update README.md for significant changes
- Add or update API documentation for new or modified endpoints
- Include JSDoc comments for TypeScript functions and components
- Update the user guide in `/docs` for user-facing changes

## Pull Request Process

### PR Template

When creating a pull request, please fill out the PR template completely, including:

- A clear description of the changes
- Link to the related issue(s)
- Testing steps and expected results
- Screenshots or videos for UI changes
- Any breaking changes or dependencies
- Checklist of completed items

### Code Review

The code review process:

1. Automated checks must pass (linting, tests, build)
2. At least one maintainer must approve the changes
3. All review comments must be addressed
4. Changes requested by reviewers must be implemented

Review feedback should be addressed by:
- Updating the PR with requested changes
- Discussing alternatives if you disagree with feedback
- Marking comments as resolved once addressed

### CI/CD Process

Our CI/CD pipeline includes:

1. **Continuous Integration**:
   - Linting and code style checks
   - Unit and integration tests
   - Security vulnerability scanning
   - Bundle size checks for frontend

2. **Deployment**:
   - Automatic deployment to staging for merges to `develop`
   - Automatic deployment to production for merges to `main`
   - Post-deployment smoke tests

## Architecture Guidelines

### Frontend Architecture

- **Project Structure**:
  ```
  frontend/
  ├── public/           # Static assets
  ├── src/
  │   ├── assets/       # Images, fonts, etc.
  │   ├── components/   # Reusable UI components
  │   ├── context/      # React Context providers
  │   ├── hooks/        # Custom React hooks
  │   ├── pages/        # Page components
  │   ├── types/        # TypeScript type definitions
  │   └── utils/        # Utility functions
  ```

- **Best Practices**:
  - Use functional components with hooks
  - Implement proper error handling and loading states
  - Follow responsive design principles
  - Use TypeScript for type safety
  - Extract reusable logic into custom hooks
  - Limit component responsibilities (Single Responsibility Principle)

### Backend Architecture

- **Project Structure**:
  ```
  backend/
  ├── app/
  │   ├── api/          # API routes and controllers
  │   ├── auth/         # Authentication logic
  │   ├── converters/   # File conversion logic
  │   ├── models/       # Database models
  │   └── utils/        # Utility functions
  ├── tests/            # Test files
  └── migrations/       # Database migrations
  ```

- **Best Practices**:
  - Follow RESTful API design patterns
  - Implement proper input validation and error handling
  - Use dependency injection for testability
  - Document API endpoints (docstrings + OpenAPI/Swagger)
  - Implement rate limiting and security best practices
  - Write meaningful error messages

### Creating a New Converter

If you're adding support for a new file format:

1. Create a new converter in `backend/app/converters/` that extends `BaseConverter`:
   ```python
   from app.converters.base_converter import BaseConverter
   
   class NewFormatConverter(BaseConverter):
       """Converter for NewFormat files."""
       
       def supports_source_format(self, source_format):
           """Check if this converter supports the source format."""
           return source_format.lower() in ['new_format', 'nft']
           
       def supports_target_format(self, target_format):
           """Check if this converter supports the target format."""
           return target_format.lower() in ['pdf', 'png', 'jpg']
           
       def convert(self, source_path, target_path, options=None):
           """Convert the file from source format to target format."""
           # Implement conversion logic here
           pass
   ```

2. Register your converter in `converter_factory.py`:
   ```python
   from app.converters.new_format_converter import NewFormatConverter
   
   # In the ConverterFactory initialization
   self.register_converter(NewFormatConverter())
   ```

3. Add appropriate tests in `tests/converters/`:
   ```python
   def test_new_format_converter():
       """Test the NewFormat converter."""
       converter = NewFormatConverter()
       
       # Test format support
       assert converter.supports_source_format('new_format')
       assert converter.supports_target_format('pdf')
       
       # Test conversion
       # ...
   ```

4. Update documentation to reflect the new supported format
   - Add to README.md
   - Update API documentation
   - Update user documentation

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

---

Thank you for contributing to File Converter! If you have any questions, feel free to reach out to the maintainers.

Maintained by [Mahmoud Ashraf (SNO7E)](https://github.com/SNO7E-G) 