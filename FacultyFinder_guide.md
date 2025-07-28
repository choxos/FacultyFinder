# FacultyFinder Development Guide

FacultyFinder is a standalone academic collaboration platform that helps researchers discover ideal faculty collaborators worldwide. This guide outlines the development approach, theme system, and project structure.

## Theme System

FacultyFinder uses a custom theme system focused on academic professionalism and global accessibility. The main theme file is located at `webapp/static/css/facultyfinder.css` and includes:

### Color Palette
- **Primary Blue**: Academic trust and professionalism
- **Secondary Gold**: Excellence and achievement 
- **Accent Green**: Growth and collaboration
- **Neutral Grays**: Clean, readable interface

### CSS Variables
The theme uses CSS custom properties with the `--ff-` prefix:
- `--ff-primary`: Main brand color
- `--ff-secondary`: Secondary accent
- `--ff-bg-primary`: Background colors
- `--ff-text-primary`: Text colors
- `--ff-border-color`: Border colors

### Dark Mode Support
Full dark theme implementation using `[data-theme="dark"]` attribute with:
- Optimized contrast ratios
- Academic-appropriate color schemes
- Consistent component styling

## Project Structure

```
FacultyFinder/
├── webapp/                 # Main web application
│   ├── app.py             # Flask application core
│   ├── templates/         # Jinja2 HTML templates
│   ├── static/            # CSS, JS, and assets
│   └── wsgi.py           # Production WSGI entry
├── database/              # Schema and database files
├── scripts/              # Data processing utilities
├── data/                 # Raw academic data
└── docs/                 # Documentation
```

## Development Philosophy

1. **Academic Focus**: Every feature designed for researchers and academics
2. **Global Accessibility**: Multi-language support and international standards
3. **Data Integrity**: Rigorous validation of academic information
4. **Privacy First**: Respect for faculty privacy and academic freedom
5. **Performance**: Optimized for large-scale academic databases

## Key Features Implementation

### Faculty Discovery
- Advanced search with multiple filters
- AI-powered matching algorithms
- Publication metrics integration
- Collaboration network visualization

### University Profiles
- Global coverage with local relevance
- Department-level insights
- Geographic integration
- Multi-language support

### API System
- RESTful endpoints for all data
- Authentication and rate limiting
- Comprehensive documentation
- Developer-friendly SDK examples

## Getting Started

1. **Environment Setup**: Follow the installation guide in README.md
2. **Database Initialization**: Run the data loader scripts
3. **Theme Customization**: Modify CSS variables in facultyfinder.css
4. **Feature Development**: Use the component system for consistency

## Contributing Guidelines

- Follow academic data standards
- Maintain theme consistency
- Test across multiple browsers
- Document new features thoroughly
- Respect privacy requirements

---

For detailed setup instructions, see the main README.md file.