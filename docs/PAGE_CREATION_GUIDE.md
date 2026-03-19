# Ava Digital Page Creation Guide

## How to Create New Pages That Match the Site Design

### Overview
All Ava Digital pages use a **custom HTML template** with the `elementor_canvas` template. This bypasses the WordPress theme and gives full control over the design.

### Key Components of the Template

#### 1. **Template Type**
- Must use: `"template": "elementor_canvas"`
- This removes WordPress theme header/footer interference

#### 2. **CSS Variables (Colors)**
```css
:root {
  --navy: #0a0f1e;        /* Main background */
  --navy2: #111827;       /* Card/section backgrounds */
  --navy3: #1e293b;       /* Borders */
  --accent: #6366f1;      /* Primary buttons/links */
  --accent2: #818cf8;     /* Secondary accent */
  --green: #10b981;       /* Success/positive */
  --white: #ffffff;       /* Text on dark */
  --gray: #94a3b8;        /* Body text */
  --border: rgba(255,255,255,0.08); /* Subtle borders */
}
```

#### 3. **Required Header Section**
```html
<nav>
  <a href="https://avadigitalagency.com/" class="nav-logo">ava <span>digital</span></a>
  <a href="#cta" class="nav-cta">Book a Call →</a>
</nav>
```

#### 4. **Required Hero Section**
```html
<div class="hero">
  <div class="hero-badge">📚 [Category]</div>
  <h1>[Page Title] <span class="grad">[Highlighted Word]</span></h1>
  <p class="hero-sub">[Subtitle/description]</p>
  <a href="#cta" class="btn-primary">Get Your Free Audit →</a>
</div>
```

#### 5. **Content Section Structure**
```html
<section>
  <h2>📊 [Section Title]</h2>
  <p>[Paragraph text]</p>
  <ul>
    <li><strong>💸 [Bold Label]:</strong> [Description]</li>
  </ul>
  
  <h3>1️⃣ [Subsection Title]</h3>
  <p>[Content]</p>
</section>
```

#### 6. **CTA Box (Required)**
```html
<div class="cta-box" id="cta">
  <h2>🚀 [CTA Headline]</h2>
  <p>[CTA description]</p>
  <a href="/contact" class="btn-primary">Book Your Free Consultation →</a>
</div>
```

#### 7. **FAQ Section (Optional)**
```html
<h2>❓ Frequently Asked Questions</h2>
<div class="faq-item">
  <h3>[Question]</h3>
  <p>[Answer]</p>
</div>
```

#### 8. **Required Footer**
```html
<footer>
  <div class="footer-grid">
    <div class="footer-brand">
      <a href="https://avadigitalagency.com/" class="nav-logo">ava <span>digital</span></a>
      <p>AI-powered digital marketing for Illinois businesses...</p>
    </div>
    <div class="footer-col">
      <h4>Services</h4>
      <ul><!-- Service links --></ul>
    </div>
    <div class="footer-col">
      <h4>Cities</h4>
      <ul><!-- City links --></ul>
    </div>
    <div class="footer-col">
      <h4>Company</h4>
      <ul><!-- Company links --></ul>
    </div>
  </div>
  <div class="footer-bottom">
    <span>© 2026 Ava Digital Agency. All rights reserved.</span>
    <span>AI-Powered Digital Marketing</span>
  </div>
</footer>
```

### Critical CSS Rules

**Headings must be WHITE:**
```css
h1, h2, h3 { color: white; }
```

**Hero H1 specific:**
```css
.hero h1 { 
  font-size: 52px; 
  font-weight: 900; 
  color: white;  /* CRITICAL - must be explicit */
}
.hero h1 .grad {
  background: linear-gradient(135deg, var(--accent2), #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Publishing via WordPress API

**Endpoint:**
```
POST https://avadigitalagency.com/wp-json/wp/v2/pages
```

**Headers:**
```
Content-Type: application/json
Authorization: Basic [username]:[app_password]
```

**Request Body:**
```json
{
  "title": "Page Title",
  "content": "<!-- Full HTML content here -->",
  "status": "publish",
  "slug": "page-url-slug",
  "template": "elementor_canvas"
}
```

### WordPress Credentials
- **Username:** vikmehta
- **App Password:** Ivx0 otYS SAJO 3iLS xpVi 9KyW
- **Site:** https://avadigitalagency.com

### Common Mistakes to Avoid

1. **Missing `color: white` on headings** - They'll be invisible on dark background
2. **Not using `elementor_canvas` template** - WordPress theme will interfere
3. **Forgetting the CTA section with `id="cta"`** - "Book a Call" button won't work
4. **Not including the full HTML structure** - Missing head/body tags
5. **Using WordPress blocks instead of HTML** - Breaks the custom design

### Example: Complete Page JSON

See file: `/templates/EXAMPLE_PAGE.json` for a full working example.

### Live Examples to Reference

1. **How to Choose a Digital Marketing Agency**
   - URL: https://avadigitalagency.com/how-to-choose-digital-marketing-agency/
   - Page ID: 23934

2. **Outbound Email Marketing** (Original template)
   - URL: https://avadigitalagency.com/outbound-email-marketing/
   - Page ID: 23517

### Quick Checklist for New Pages

- [ ] Full HTML5 doctype and structure
- [ ] `elementor_canvas` template set
- [ ] Navy color scheme variables
- [ ] White text on all headings (h1, h2, h3)
- [ ] Navigation bar with logo
- [ ] Hero section with badge, title, subtitle, CTA
- [ ] Content sections with emojis
- [ ] CTA box with `id="cta"`
- [ ] FAQ section (if needed)
- [ ] Footer with all links
- [ ] Mobile responsive CSS
- [ ] Yoast SEO meta tags

---

**Last Updated:** March 19, 2026
**Created By:** Lola
