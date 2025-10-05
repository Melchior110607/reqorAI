# B2B Request Management SaaS

A modern web application for managing B2B requests between companies, built with FastAPI backend and Next.js frontend.

## Features

### Core Features
- **User Authentication**: JWT-based authentication with registration and login
- **Dashboard**: Overview of all requests with statistics and priority items
- **Request Management**: 
  - Outgoing requests (requests sent to clients)
  - Incoming requests (requests received from clients)
  - Status tracking (pending, completed, overdue)
  - Priority system with visual indicators
  - Due dates and reminder frequencies
  - Detailed request views with editing capabilities
- **Client Management**: Add, edit, and manage business clients
- **User Profile**: Account information and activity history
- **Modern UI**: Responsive design with Tailwind CSS

### AI-Powered Features
- **Email Integration**: Connect Gmail and Outlook accounts
- **Automatic Email Processing**: Real-time email interception and processing
- **Client Recognition**: Advanced algorithm to match emails to existing clients
- **AI Classification**: GPT-4 powered email classification and analysis
- **Smart Actions**: Automatic request updates based on email content
- **Reminder System**: Automated email reminders for outgoing requests

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Database
- **JWT**: Authentication
- **Pydantic**: Data validation
- **OpenAI GPT-4**: AI classification and analysis
- **Gmail API**: Email integration
- **Microsoft Graph API**: Outlook integration
- **Redis**: Caching and background jobs
- **Celery**: Asynchronous task processing

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Headless UI**: Accessible components
- **Axios**: HTTP client

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd projectAI
```

2. Start all services:
```bash
docker-compose up -d
```

3. The application will be available at:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/b2b_requests"
export JWT_SECRET="your-secret-key"

# Start the server
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### Database Setup
Make sure PostgreSQL is running and create the database:
```sql
CREATE DATABASE b2b_requests;
```

The database tables will be created automatically when the backend starts.

## API Documentation

The API documentation is automatically generated and available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
projectAI/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── auth/          # Authentication
│   │   ├── database/      # Database configuration
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── main.py        # FastAPI application
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages (App Router)
│   │   ├── components/    # React components
│   │   ├── contexts/      # React contexts
│   │   ├── services/      # API services
│   │   ├── types/         # TypeScript types
│   │   └── utils/         # Utility functions
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Usage

1. **Register**: Create a new account with your company information
2. **Add Clients**: Add your business clients and their contact information
3. **Create Requests**: 
   - Outgoing: Requests you send to clients
   - Incoming: Requests clients send to you
4. **Track Progress**: Update request statuses and priorities
5. **Dashboard**: Monitor all requests and get insights

## Environment Variables

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT tokens
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `JWT_EXPIRATION_HOURS`: Token expiration time (default: 24)
- `OPENAI_API_KEY`: OpenAI API key for AI classification
- `GMAIL_CLIENT_ID`: Gmail OAuth client ID
- `GMAIL_CLIENT_SECRET`: Gmail OAuth client secret
- `OUTLOOK_CLIENT_ID`: Outlook OAuth client ID
- `OUTLOOK_CLIENT_SECRET`: Outlook OAuth client secret
- `REDIS_URL`: Redis connection string
- `BASE_URL`: Base URL for OAuth callbacks

### Frontend
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
