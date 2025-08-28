# E-Commerce Platform

A full-stack e-commerce platform built with Next.js, Django, TailwindCSS, and PostgreSQL.

## Features

### User Authentication
- User registration and login
- Password reset functionality
- Profile management
- Secure authentication using JWT

### Product Management
- Product listing with categories
- Product search and filtering
- Product details page
- Admin panel for product management

### Shopping Cart
- Add/remove items from cart
- Update item quantities
- Cart persistence across sessions

### Checkout Process
- Shipping information
- Order summary
- Payment integration (simulated for development)
- Order confirmation

### Admin Features
- Custom admin interface
- Product CRUD operations
- User management
- Order management

## Tech Stack

### Frontend
- Next.js 14
- React 18
- TypeScript
- TailwindCSS
- Redux Toolkit (State Management)
- React Hook Form (Form handling)

### Backend
- Django 5.0
- Django REST Framework
- PostgreSQL
- JWT Authentication
- Django CORS Headers

## Prerequisites

- Node.js 18+ (LTS recommended)
- Python 3.10+
- PostgreSQL 14+
- npm or yarn
- pip (Python package manager)

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Update the .env file with your configuration
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Set up environment variables:
   ```bash
   cp .env.local.example .env.local
   # Update the .env.local file with your configuration
   ```

4. Run the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
ecommerce/
├── backend/                 # Django backend
│   ├── config/             # Django project settings
│   ├── apps/               # Django apps
│   │   ├── accounts/       # User authentication
│   │   ├── products/       # Product management
│   │   ├── cart/          # Shopping cart
│   │   └── orders/        # Order processing
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/               # Next.js frontend
│   ├── public/            # Static files
│   ├── src/
│   │   ├── app/          # App router
│   │   ├── components/    # Reusable components
│   │   ├── lib/          # Utility functions
│   │   ├── store/        # Redux store
│   │   └── styles/       # Global styles
│   ├── package.json
│   └── next.config.js
│
└── README.md              # This file
```

## Environment Variables

### Backend (`.env`)

```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/ecommerce
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (`.env.local`)

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=your-stripe-public-key
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/auth/register/ | POST | User registration |
| /api/auth/login/ | POST | User login |
| /api/auth/me/ | GET | Get current user |
| /api/products/ | GET | List all products |
| /api/products/<id>/ | GET | Get product details |
| /api/cart/ | GET, POST | Get or update cart |
| /api/orders/ | POST | Create new order |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Next.js Documentation](https://nextjs.org/docs)
- [Django Documentation](https://docs.djangoproject.com/)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
