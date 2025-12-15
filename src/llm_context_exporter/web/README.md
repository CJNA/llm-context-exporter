# LLM Context Exporter Web Interface

This directory contains the web interface for the LLM Context Exporter, providing a user-friendly way to export ChatGPT context to Gemini or local LLMs.

## Features

- **Clean, minimal design** with responsive layout
- **Drag-and-drop file upload** for ChatGPT exports
- **Interactive preview** of extracted context
- **Filtering capabilities** for projects and conversations
- **Payment integration** with Stripe (configurable)
- **Beta user management** with feedback collection
- **Platform-specific output** for Gemini and Ollama
- **Validation test generation** for context verification

## Architecture

### Frontend
- **HTML/CSS/JavaScript** - Vanilla implementation, no build step required
- **Responsive design** - Works on desktop and tablets
- **Progressive enhancement** - Graceful degradation without JavaScript
- **Accessibility** - Semantic HTML and keyboard navigation

### Backend
- **Flask** - Lightweight Python web framework
- **Local-only processing** - All data stays on user's machine
- **Session management** - Automatic cleanup after 1 hour
- **Rate limiting** - 100 requests per hour per IP
- **CSRF protection** - Built-in security measures

## File Structure

```
web/
├── app.py              # Flask application and API routes
├── beta.py             # Beta user management
├── payment.py          # Payment processing (Stripe)
├── templates/
│   └── index.html      # Main HTML template
├── static/
│   ├── css/
│   │   └── styles.css  # All CSS styles
│   └── js/
│       └── app.js      # Frontend JavaScript application
└── README.md           # This file
```

## API Endpoints

### Core Functionality
- `GET /` - Serve web interface
- `POST /api/upload` - Upload and parse ChatGPT export
- `GET /api/preview` - Get preview of extracted context
- `POST /api/filter` - Apply filters to context
- `POST /api/generate` - Generate output for target platform
- `GET /api/download/<id>` - Download generated files
- `POST /api/validate` - Generate validation tests

### Payment & Beta
- `POST /api/payment/create` - Create Stripe payment intent
- `POST /api/payment/verify` - Verify payment completion
- `POST /api/payment/webhook` - Handle Stripe webhooks
- `GET /api/beta/status` - Check beta user status
- `POST /api/beta/feedback` - Submit beta user feedback

## Usage

### Development
```bash
# Start development server
python -m llm_context_exporter.web.app

# Or use the test script
python test_web_interface.py
```

### Production
```bash
# Use a production WSGI server like Gunicorn
gunicorn -w 4 -b 127.0.0.1:8080 llm_context_exporter.web.app:create_app()
```

## Configuration

### Environment Variables
- `SECRET_KEY` - Flask secret key for sessions
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret
- `FLASK_DEBUG` - Enable debug mode (development only)

### Payment Configuration
The payment system is optional and can be disabled by not setting Stripe keys. When disabled:
- All users get free access (like CLI)
- Payment pages are skipped
- Beta user features still work

### Beta User Management
Beta users are managed via SQLite database at `~/.llm_context_exporter_beta.db`:
- Whitelist-based access control
- Usage tracking and analytics
- Feedback collection with ratings
- Admin interface for user management

## Security Features

### Privacy Protection
- **Local-only processing** - No data sent to external services
- **Session isolation** - Each user's data is separate
- **Automatic cleanup** - Files deleted after 1 hour
- **Localhost binding** - Server only accessible from local machine

### Security Measures
- **Rate limiting** - Prevents abuse
- **File size limits** - 500MB maximum upload
- **File type validation** - Only ZIP and JSON allowed
- **CSRF protection** - Built-in Flask security
- **Input sanitization** - All user input validated

## Browser Support

### Supported Browsers
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

### Required Features
- ES6 JavaScript
- CSS Grid and Flexbox
- Fetch API
- File API with drag-and-drop
- Clipboard API (for copy functionality)

## Customization

### Styling
All styles are in `static/css/styles.css` using CSS custom properties for easy theming:
```css
:root {
  --primary-color: #667eea;
  --secondary-color: #764ba2;
  --success-color: #10b981;
  --error-color: #ef4444;
}
```

### Branding
Update the header section in `templates/index.html`:
```html
<h1 class="logo">Your Brand Name</h1>
<p class="tagline">Your custom tagline</p>
```

### Payment Integration
To enable Stripe payments:
1. Set environment variables for Stripe keys
2. Update JavaScript with your publishable key
3. Configure webhook endpoint in Stripe dashboard
4. Test with Stripe test cards

## Testing

### Manual Testing
1. Run `python test_web_interface.py`
2. Upload a sample ChatGPT export file
3. Test the complete flow from upload to download
4. Verify responsive design on different screen sizes

### Automated Testing
```bash
# Run Flask API integration tests
python -m pytest tests/test_flask_api_integration.py

# Run with coverage
python -m pytest tests/test_flask_api_integration.py --cov=src/llm_context_exporter/web
```

## Deployment

### Local Deployment
The web interface is designed to run locally for privacy. Users can:
1. Install the package: `pip install llm-context-exporter`
2. Start web interface: `llm-context-export --web`
3. Access at `http://127.0.0.1:8080`

### Hosted Deployment (Optional)
For organizations wanting to host the service:
1. Use HTTPS with proper certificates
2. Configure Stripe for production payments
3. Set up proper logging and monitoring
4. Implement backup for beta user database
5. Consider load balancing for multiple instances

## Troubleshooting

### Common Issues

**"Template not found" error**
- Ensure templates directory exists in web module
- Check Flask template_folder configuration

**Static files not loading**
- Verify static directory structure
- Check Flask static_folder configuration
- Ensure files have correct permissions

**Payment not working**
- Verify Stripe keys are set correctly
- Check browser console for JavaScript errors
- Ensure webhook endpoint is configured

**Upload failing**
- Check file size (500MB limit)
- Verify file type (ZIP or JSON only)
- Check available disk space

### Debug Mode
Enable debug mode for development:
```bash
export FLASK_DEBUG=true
python -m llm_context_exporter.web.app
```

This provides:
- Detailed error messages
- Automatic reloading on code changes
- Interactive debugger in browser